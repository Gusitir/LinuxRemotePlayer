#!/bin/bash
set -e

# P7: Release process
# 1. Bump version in VERSION file.
# 2. Run ./scripts/build_deb.sh
# 3. Upload dist/linuxremoteplayer_<VERSION>_amd64.deb to website/downloads/
# 4. Update website/latest.json with new version, url, and sha256.

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f "VERSION" ]; then
    echo "VERSION file not found! (e.g. echo 1.1.0 > VERSION)"
    exit 1
fi
VERSION=$(cat VERSION)

echo "Building linuxremoteplayer_${VERSION}_amd64.deb..."

echo "Running CSS sync check..."
python3 scripts/check_css_sync.py

# Clean old dist
rm -rf pkg dist
mkdir -p dist

# Create staging directories
mkdir -p pkg/opt/linuxremoteplayer
mkdir -p pkg/DEBIAN
mkdir -p pkg/usr/local/bin
mkdir -p pkg/etc/sudoers.d
mkdir -p pkg/usr/share/applications
mkdir -p pkg/usr/share/icons/hicolor/512x512/apps

cp frontend/icon-512.png pkg/usr/share/icons/hicolor/512x512/apps/linuxremoteplayer.png

cat <<EOF > pkg/usr/share/applications/linuxremoteplayer-panel.desktop
[Desktop Entry]
Type=Application
Name=LinuxRemotePlayer
Comment=Panel de estado y emparejamiento
Exec=xdg-open https://127.0.0.1:8000/status
Icon=linuxremoteplayer
Categories=AudioVideo;Video;Player;
Terminal=false
EOF

# Copy core components
cp -r backend frontend scripts VERSION pkg/opt/linuxremoteplayer/

# Inject VERSION into service worker for PWA cache invalidation
sed -i "s/__LRP_VERSION__/${VERSION}/" pkg/opt/linuxremoteplayer/frontend/sw.js
grep -q "lrp-${VERSION}" pkg/opt/linuxremoteplayer/frontend/sw.js || { echo "ERROR: sw.js sin versionar"; exit 1; }

# Cleanup excluded items (secrets, caches, and dev/build-only tooling not needed at runtime)
cd pkg/opt/linuxremoteplayer
rm -rf backend/.venv backend/certs backend/.pairing_token backend/.env backend/__pycache__ \
       scripts/__pycache__ scripts/dev scripts/build_deb.sh scripts/check_css_sync.py
cd ../../..

chmod +x pkg/opt/linuxremoteplayer/scripts/*.sh
chmod 0755 pkg/opt/linuxremoteplayer/scripts/debian/*.sh

# DEBIAN/control
cat <<EOF > pkg/DEBIAN/control
Package: linuxremoteplayer
Version: ${VERSION}
Architecture: amd64
Maintainer: LinuxRemotePlayer
Description: LinuxRemotePlayer API and web interface
Depends: python3, python3-venv, python3-dev, build-essential, openssl, sudo, curl, ca-certificates, python3-cryptography
Recommends: firefox-esr, ufw, pulseaudio-utils
EOF

# DEBIAN/postinst
cat <<'EOF' > pkg/DEBIAN/postinst
#!/bin/bash
set -e

BACKEND_DIR=/opt/linuxremoteplayer/backend
cd "$BACKEND_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
set +e
if ! .venv/bin/pip install -r requirements.txt; then
    echo "[!] Advertencia: falló pip install. Dependencias incompletas."
    touch /opt/linuxremoteplayer/.deps_incomplete
fi
set -e

# ASTRA-01: Ensure root:root ownership and 0755/0644 on /opt/linuxremoteplayer and .venv
chown -R root:root /opt/linuxremoteplayer
find /opt/linuxremoteplayer -type d -exec chmod 0755 {} +
find /opt/linuxremoteplayer -type f -exec chmod 0644 {} +
find /opt/linuxremoteplayer/scripts -type f -name "*.sh" -exec chmod 0755 {} +
if [ -d /opt/linuxremoteplayer/backend/.venv/bin ]; then
    chmod 0755 /opt/linuxremoteplayer/backend/.venv/bin/*
fi

# Ensure /var/lib/linuxremoteplayer exists and is owned by lrp:lrp 0700
if id -u lrp >/dev/null 2>&1; then
    mkdir -p /var/lib/linuxremoteplayer
    for _f in .env .pairing_token .license_cache; do
        if [ -f "/opt/linuxremoteplayer/backend/$_f" ] && [ ! -f "/var/lib/linuxremoteplayer/$_f" ]; then
            cp -p "/opt/linuxremoteplayer/backend/$_f" "/var/lib/linuxremoteplayer/$_f"
            rm -f "/opt/linuxremoteplayer/backend/$_f"
        fi
    done
    if [ -d "/opt/linuxremoteplayer/backend/certs" ] && [ ! -d "/var/lib/linuxremoteplayer/certs" ]; then
        cp -rp "/opt/linuxremoteplayer/backend/certs" "/var/lib/linuxremoteplayer/certs"
        rm -rf "/opt/linuxremoteplayer/backend/certs"
    fi
    chown -R lrp:lrp /var/lib/linuxremoteplayer
    chmod 0700 /var/lib/linuxremoteplayer
fi

# Create lrp-setup
cat <<'INNEREOF' > /usr/local/bin/lrp-setup
#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo lrp-setup)"
  exit 1
fi
cd /opt/linuxremoteplayer/scripts
exec ./debian/bootstrap.sh "$@"
INNEREOF
chmod 755 /usr/local/bin/lrp-setup
if grep -q '^phase=complete$' /var/lib/linuxremoteplayer/bootstrap/state 2>/dev/null \
   && grep -q '^phase=complete$' /var/lib/linuxremoteplayer/session/state 2>/dev/null \
   && command -v systemd-run >/dev/null 2>&1; then
    systemd-run --unit="linuxremoteplayer-bootstrap-ota-$$" --on-active=30s --no-block \
        /usr/local/bin/lrp-setup --resume --unattended || true
fi

# Create lrp-update wrapper
cat <<'INNEREOF' > /usr/local/bin/lrp-update
#!/bin/bash
# ATENCION AL QUE EDITE ESTE SCRIPT --------------------------------------------
# Todo el cuerpo vive dentro de funciones y la ultima linea es  main "$@"; exit $?
# Eso NO es estilo: es lo unico que impide un bug real. Este script llama a
# `apt-get install --reinstall`, y el postinst de ese paquete REESCRIBE este mismo
# archivo. Bash lee los scripts por posicion de byte, asi que si el codigo estuviera
# suelto, al volver del apt bash retomaria en un offset del archivo NUEVO, leeria un
# fragmento a mitad de palabra y moriria antes de reiniciar el servicio. Paso de
# verdad en el OTA 1.8.9->1.8.10: quedo `inactive (dead)`.
# Con funciones, bash parsea el archivo entero ANTES de ejecutar.
# El `; exit $?` va en la MISMA linea que main a proposito: asi bash ya lo tiene
# parseado antes de que el archivo cambie. Si lo pasas a la linea de abajo, el bug vuelve.
# ------------------------------------------------------------------------------

restart_services() {
    local rc=$?
    echo "[i] Asegurando que el servicio quede levantado (rc=$rc)..."
    systemctl daemon-reload || true
    systemctl enable linuxremoteplayer.service || true
    systemctl restart linuxremoteplayer.service || true
    return $rc
}

rollback_ota() {
    echo "[!] ERROR CRITICO: Health check fallo tras la actualizacion (watchdog 45s). Iniciando rollback transaccional..." >&2
    local backup_dir="/var/lib/linuxremoteplayer/ota-backup"
    if [ -d "$backup_dir/opt" ]; then
        echo "[!] Restaurando /opt/linuxremoteplayer desde $backup_dir/opt..."
        rm -rf /opt/linuxremoteplayer
        cp -rp "$backup_dir/opt" /opt/linuxremoteplayer
    fi
    systemctl daemon-reload || true
    systemctl restart linuxremoteplayer.service || true
    echo "[!] Rollback completado. Servicio restaurado a version previa." >&2
    exit 1
}

check_anti_downgrade() {
    local REMOTE_VER="$1"
    local LOCAL_VER="$2"

    if [ -z "$REMOTE_VER" ]; then
        echo "[!] ERROR: Version remota no especificada." >&2
        exit 1
    fi

    if [ -z "$LOCAL_VER" ]; then
        echo "[i] Sin version local previa; permitiendo instalacion."
        return 0
    fi

    if command -v dpkg >/dev/null 2>&1; then
        if ! dpkg --compare-versions "$REMOTE_VER" gt "$LOCAL_VER"; then
            echo "[!] ERROR: Proteccion anti-downgrade. Version remota ($REMOTE_VER) no es estrictamente mayor que local ($LOCAL_VER)." >&2
            exit 1
        fi
    else
        if [ "$REMOTE_VER" = "$LOCAL_VER" ]; then
            echo "[!] ERROR: Version remota ($REMOTE_VER) no es estrictamente mayor que local ($LOCAL_VER)." >&2
            exit 1
        fi
    fi
}

verify_ed25519_signature() {
    local manifest_str="$1"
    local PUBKEY_FILE="/opt/linuxremoteplayer/scripts/debian/lrp-ota-pub.pem"

    if [ ! -f "$PUBKEY_FILE" ]; then
        echo "[!] ERROR: Clave publica OTA no encontrada en $PUBKEY_FILE" >&2
        exit 1
    fi

    local SIGNATURE
    SIGNATURE=$(echo "$manifest_str" | grep -o '"signature"\s*:\s*"[^"]*"' | cut -d'"' -f4 || true)
    if [ -z "$SIGNATURE" ]; then
        echo "[!] ERROR: Manifiesto OTA sin firma criptografica Ed25519." >&2
        exit 1
    fi

    local VERSION ARCH FILENAME SHA256 URL
    VERSION=$(echo "$manifest_str" | grep -o '"version"\s*:\s*"[^"]*"' | cut -d'"' -f4 || true)
    ARCH=$(echo "$manifest_str" | grep -o '"architecture"\s*:\s*"[^"]*"' | cut -d'"' -f4 || true)
    URL=$(echo "$manifest_str" | grep -o '"deb_url"\s*:\s*"[^"]*"' | cut -d'"' -f4 || true)
    [ -n "$URL" ] || URL=$(echo "$manifest_str" | grep -o '"url"\s*:\s*"[^"]*"' | cut -d'"' -f4 || true)
    FILENAME=$(echo "$manifest_str" | grep -o '"filename"\s*:\s*"[^"]*"' | cut -d'"' -f4 || true)
    [ -n "$FILENAME" ] || FILENAME=$(basename "$URL")
    SHA256=$(echo "$manifest_str" | grep -o '"sha256"\s*:\s*"[^"]*"' | cut -d'"' -f4 || true)

    local PAYLOAD_FILE="/tmp/lrp-ota-payload.$$.tmp"
    local SIG_BIN="/tmp/lrp-ota-sig.$$.tmp"

    printf "%s" "${VERSION}|${ARCH}|${FILENAME}|${SHA256}|${URL}" > "$PAYLOAD_FILE"
    if ! echo "$SIGNATURE" | base64 -d > "$SIG_BIN" 2>/dev/null; then
        rm -f "$PAYLOAD_FILE" "$SIG_BIN"
        echo "[!] ERROR: No se pudo decodificar la firma base64." >&2
        exit 1
    fi

    if ! openssl pkeyutl -verify -pubin -inkey "$PUBKEY_FILE" -rawin -in "$PAYLOAD_FILE" -sigfile "$SIG_BIN" >/dev/null 2>&1; then
        rm -f "$PAYLOAD_FILE" "$SIG_BIN"
        echo "[!] ERROR CRITICO: Verificacion de firma Ed25519 FALLO. Manifiesto adulterado o invalido." >&2
        exit 1
    fi

    rm -f "$PAYLOAD_FILE" "$SIG_BIN"
    echo "[+] Firma Ed25519 del manifiesto verificada exitosamente."
}

main() {
    if [ -z "$LRP_DETACHED" ] && command -v systemd-run >/dev/null; then
        exec systemd-run --collect --unit=lrp-update-job --setenv=LRP_DETACHED=1 /usr/local/bin/lrp-update
    fi

    # H18: el log va a /var/log y no a /tmp. En /tmp cualquier usuario puede haber dejado
    # antes un archivo con ese nombre, y entonces el actualizador -- que corre como root
    # dentro de una unidad transiente -- no puede escribirlo y el log queda mudo justo
    # cuando mas se lo necesita. /var/log es root-only y ademas queda fuera del alcance de
    # PrivateTmp. El script sobrevive igual si falla (este exec va ANTES del `set -e`).
    exec >>/var/log/lrp-update.log 2>&1

    # El servicio se reinicia SIEMPRE, salga como salga la actualizacion. Un fallo
    # bajando el .deb no puede dejar al usuario sin control remoto.
    trap restart_services EXIT

    set -e
    export DEBIAN_FRONTEND=noninteractive
    ENV_FILE=/var/lib/linuxremoteplayer/.env
    [ -f "$ENV_FILE" ] || ENV_FILE=/opt/linuxremoteplayer/backend/.env
    CHANNEL="stable"
    if [ -f "$ENV_FILE" ]; then
        CHANNEL=$(awk '
            match($0, /^[[:space:]]*LRP_CHANNEL[[:space:]]*=/) {
                value = substr($0, RSTART + RLENGTH)
                sub(/^[[:space:]]*/, "", value)
                sub(/[[:space:]]*$/, "", value)
                channel = value
            }
            END { print (channel == "beta" ? "beta" : "stable") }
        ' "$ENV_FILE")
    fi
    if [ "$CHANNEL" = "beta" ]; then
        MANIFEST_URL="https://www.linuxremoteplayer.com/beta/latest.json"
    else
        MANIFEST_URL="https://www.linuxremoteplayer.com/latest.json"
    fi
    echo "Checking $MANIFEST_URL for updates..."
    LATEST_JSON=$(curl -fsSL "$MANIFEST_URL")
    VERSION=$(echo "$LATEST_JSON" | grep -o '"version"\s*:\s*"[^"]*"' | cut -d'"' -f4)
    DEB_URL=$(echo "$LATEST_JSON" | grep -o '"deb_url"\s*:\s*"[^"]*"' | cut -d'"' -f4)
    SHA256=$(echo "$LATEST_JSON" | grep -o '"sha256"\s*:\s*"[^"]*"' | cut -d'"' -f4)

    # Anti-Downgrade & Firma Ed25519
    LOCAL_VER=""
    if [ -f /opt/linuxremoteplayer/VERSION ]; then
        LOCAL_VER=$(tr -d '[:space:]' < /opt/linuxremoteplayer/VERSION)
    fi
    check_anti_downgrade "$VERSION" "$LOCAL_VER"
    verify_ed25519_signature "$LATEST_JSON"

    cd /tmp
    echo "Downloading $DEB_URL..."
    # Snap-packaged curl cannot write files outside $HOME (error 23). Fall back to wget.
    if ! curl -fsSL -o "linuxremoteplayer_${VERSION}.deb" "$DEB_URL" 2>/dev/null; then
        echo "[!] curl no pudo escribir el archivo (¿curl de snap?). Intentando con wget..."
        wget -qO "linuxremoteplayer_${VERSION}.deb" "$DEB_URL"
    fi
    if [ ! -s "linuxremoteplayer_${VERSION}.deb" ]; then
        echo "[!] ERROR: no se pudo descargar la actualización. Instala el curl real: sudo apt install curl"
        exit 1
    fi

    echo "$SHA256 linuxremoteplayer_${VERSION}.deb" | sha256sum -c -

    # Backup transaccional previo a instalacion
    BACKUP_DIR="/var/lib/linuxremoteplayer/ota-backup"
    rm -rf "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    if [ -d /opt/linuxremoteplayer ]; then
        cp -rp /opt/linuxremoteplayer "$BACKUP_DIR/opt"
    fi
    if [ -n "$LOCAL_VER" ]; then
        echo "$LOCAL_VER" > "$BACKUP_DIR/version"
    fi

    apt-get install -y --reinstall "./linuxremoteplayer_${VERSION}.deb"

    # Reiniciar servicio para que corra el nuevo codigo
    systemctl daemon-reload || true
    systemctl restart linuxremoteplayer.service || true

    # Watchdog de 45s verificando el estado del servicio levantado
    echo "[i] Iniciando watchdog de verificacion post-update (45s)..."
    HEALTH_OK=0
    for i in $(seq 1 45); do
        if curl -kfsS https://127.0.0.1:8000/health >/dev/null 2>&1 || curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
            HEALTH_OK=1
            echo "[+] Health check OK en intento $i/45."
            break
        fi
        sleep 1
    done

    if [ "$HEALTH_OK" -ne 1 ]; then
        rollback_ota
    fi

    echo "[+] Paquete $VERSION instalado y verificado. Actualizacion exitosa."
}

main "$@"; exit $?
INNEREOF
chmod 755 /usr/local/bin/lrp-update

echo "================================================="
echo " Paquete base instalado."
echo ""
echo " FALTA UN PASO. Para configurar el servicio ejecuta:"
echo "     sudo lrp-setup --apply --approve"
echo "     sudo lrp-setup --apply --approve --unattended"
echo "================================================="
EOF
chmod 755 pkg/DEBIAN/postinst

# DEBIAN/prerm
cat <<'EOF' > pkg/DEBIAN/prerm
#!/bin/bash
set -e
systemctl stop linuxremoteplayer.service 2>/dev/null || true
if [ "$1" = "remove" ]; then
    systemctl disable linuxremoteplayer.service 2>/dev/null || true
fi

# Limpieza de sistema SOLO al desinstalar de verdad. dpkg tambien corre el prerm
# en cada actualizacion con $1="upgrade": si esto se ejecutara ahi, cada OTA
# borraria las reglas udev y liberaria la licencia del dispositivo. Ver T-19.
if [ "$1" = "remove" ]; then
    if [ -x /opt/linuxremoteplayer/scripts/lrp-cleanup.sh ]; then
        /opt/linuxremoteplayer/scripts/lrp-cleanup.sh || true
    fi
fi

update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
EOF
chmod 755 pkg/DEBIAN/prerm

# sudoers
echo "%input ALL=(root) NOPASSWD: /usr/local/bin/lrp-update" > pkg/etc/sudoers.d/linuxremoteplayer
chmod 440 pkg/etc/sudoers.d/linuxremoteplayer

chmod -R 0755 pkg/DEBIAN

dpkg-deb --root-owner-group --build pkg dist/linuxremoteplayer_${VERSION}_amd64.deb
cd dist
sha256sum linuxremoteplayer_${VERSION}_amd64.deb > linuxremoteplayer_${VERSION}_amd64.deb.sha256
echo "Done! Wrote dist/linuxremoteplayer_${VERSION}_amd64.deb and sha256."
