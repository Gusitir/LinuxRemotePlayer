#!/bin/bash
# ==============================================================================
# build_iso.sh — Deterministic LRP OS Hybrid Bootable ISO Builder (Debian 13 Trixie)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

VERSION_FILE="$REPO_ROOT/VERSION"
if [ -f "$VERSION_FILE" ]; then
    VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
else
    VERSION="2.0.0"
fi

DRY_RUN=0
DEB_PATH=""
OUTPUT_ISO=""
WORKDIR=""

usage() {
    cat <<EOF
Uso: $(basename "$0") [OPCIONES]

Construye la imagen ISO booteable híbrida (BIOS/UEFI) de LRP OS basada en Debian 13 (trixie) amd64.

Opciones:
  --dry-run            Simula la configuración e inyección sin ejecutar live-build.
  --deb <path>         Ruta al archivo .deb de linuxremoteplayer a incluir.
  --output <path>      Ruta del archivo ISO de salida (default: dist/lrp-os_<VERSION>_amd64.iso).
  --workdir <dir>      Directorio temporal de trabajo para live-build.
  -h, --help           Muestra esta ayuda.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --deb)
            DEB_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_ISO="$2"
            shift 2
            ;;
        --workdir)
            WORKDIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Opción desconocida: $1" >&2
            usage
            exit 1
            ;;
    esac
done

# Validación de sistema de archivos /mnt/* (WSL / 9p / DrvFs no soportan mknod/chroot requeridos por live-build)
CURRENT_DIR="$(pwd)"
CHECK_DIR="${WORKDIR:-$CURRENT_DIR}"
if [[ "$CHECK_DIR" == /mnt/* ]] && [ "$DRY_RUN" -eq 0 ]; then
    echo "ERROR: live-build exige un sistema de archivos nativo Linux y no puede ejecutarse en /mnt/* (montaje WSL/Windows)." >&2
    echo "Ejecute el script en el filesystem nativo Linux (ej. ~/build/) o utilice --dry-run." >&2
    exit 1
fi

if [ -z "$OUTPUT_ISO" ]; then
    OUTPUT_ISO="$REPO_ROOT/dist/lrp-os_${VERSION}_amd64.iso"
fi

OUTPUT_DIR="$(dirname "$OUTPUT_ISO")"
mkdir -p "$OUTPUT_DIR"

if [ -z "$DEB_PATH" ]; then
    # Auto-detect deb in dist/
    CANDIDATE_DEB="$REPO_ROOT/dist/linuxremoteplayer_${VERSION}_amd64.deb"
    if [ -f "$CANDIDATE_DEB" ]; then
        DEB_PATH="$CANDIDATE_DEB"
    else
        # Try any deb in dist
        FOUND_DEB=$(ls "$REPO_ROOT"/dist/linuxremoteplayer_*.deb 2>/dev/null | head -n1 || true)
        if [ -n "$FOUND_DEB" ] && [ -f "$FOUND_DEB" ]; then
            DEB_PATH="$FOUND_DEB"
        else
            DEB_PATH="$CANDIDATE_DEB"
        fi
    fi
fi

if [ -z "$WORKDIR" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
        WORKDIR="/tmp/lrp-iso-build-dryrun"
    else
        WORKDIR="$(mktemp -d -t lrp-iso-XXXXXX 2>/dev/null || mktemp -d)"
    fi
fi

echo "[LRP-ISO] Preparando entorno live-build en: $WORKDIR"
echo "[LRP-ISO] Versión objetivo: $VERSION (Debian 13 trixie amd64)"
echo "[LRP-ISO] Salida ISO: $OUTPUT_ISO"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "[LRP-ISO] MODO DRY-RUN: Verificando contratos e inyección de archivos..."
fi

# Configuración de directorios de live-build
mkdir -p "$WORKDIR/auto"
mkdir -p "$WORKDIR/config/package-lists"
mkdir -p "$WORKDIR/config/hooks/live"
mkdir -p "$WORKDIR/config/bootloaders/grub-pc"
mkdir -p "$WORKDIR/config/bootloaders/isolinux"
mkdir -p "$WORKDIR/config/includes.chroot/etc/systemd"
mkdir -p "$WORKDIR/config/includes.chroot/usr/local/sbin"
mkdir -p "$WORKDIR/config/includes.chroot/tmp"
mkdir -p "$WORKDIR/config/includes.installer"

# Inyección de archivos requeridos
# 1. Package lists
cp "$SCRIPT_DIR/package-lists/lrp-appliance.list.chroot" "$WORKDIR/config/package-lists/lrp-appliance.list.chroot"

# 2. Hooks
cp "$SCRIPT_DIR/hooks/99-lrp-setup.chroot" "$WORKDIR/config/hooks/live/99-lrp-setup.chroot"
chmod +x "$WORKDIR/config/hooks/live/99-lrp-setup.chroot"

# 3. Bootloaders (GRUB & ISOLINUX)
cp "$SCRIPT_DIR/config/grub.cfg" "$WORKDIR/config/bootloaders/grub-pc/grub.cfg"
cp "$SCRIPT_DIR/config/isolinux.cfg" "$WORKDIR/config/bootloaders/isolinux/isolinux.cfg"

# 4. zram-generator config
cp "$SCRIPT_DIR/config/zram-generator.conf" "$WORKDIR/config/includes.chroot/etc/systemd/zram-generator.conf"

# 5. Installer target script
cp "$SCRIPT_DIR/installer/lrp-install-target.sh" "$WORKDIR/config/includes.chroot/usr/local/sbin/lrp-install-target.sh"
chmod +x "$WORKDIR/config/includes.chroot/usr/local/sbin/lrp-install-target.sh"

# 6. preseed.cfg
cp "$SCRIPT_DIR/preseed.cfg" "$WORKDIR/config/includes.installer/preseed.cfg"

# 7. Inyección de paquete deb local si existe
if [ -f "$DEB_PATH" ]; then
    echo "[LRP-ISO] Inyectando paquete deb: $DEB_PATH"
    cp "$DEB_PATH" "$WORKDIR/config/includes.chroot/tmp/lrp.deb"
else
    echo "[LRP-ISO] Nota: Paquete deb no encontrado en $DEB_PATH (se omite pre-instalación en staging)"
fi

# Configuración live-build (lb config)
LB_CONFIG_CMD=(
    lb config
    --binary-images iso-hybrid
    --architectures amd64
    --distribution trixie
    --debian-installer live
    --archive-areas "main contrib non-free non-free-firmware"
    --bootloader grub-efi
    --iso-application "LinuxRemotePlayer OS"
    --iso-publisher "LinuxRemotePlayer Project"
    --iso-volume "LRP_OS_${VERSION}"
)

echo "[LRP-ISO] Comando lb config planificado:"
echo "  ${LB_CONFIG_CMD[*]}"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "[LRP-ISO] DRY-RUN exitoso: todas las configuraciones, hooks, package-lists y contratos verificados."
    exit 0
fi

if ! command -v lb >/dev/null 2>&1; then
    echo "ERROR: live-build (comando 'lb') no está instalado. Ejecute: sudo apt-get install -y live-build" >&2
    exit 1
fi

cd "$WORKDIR"
echo "[LRP-ISO] Ejecutando lb config..."
"${LB_CONFIG_CMD[@]}"

echo "[LRP-ISO] Ejecutando lb build..."
lb build

GENERATED_ISO=$(ls "$WORKDIR"/live-image-amd64.hybrid.iso "$WORKDIR"/*.iso 2>/dev/null | head -n1 || true)
if [ -z "$GENERATED_ISO" ] || [ ! -f "$GENERATED_ISO" ]; then
    echo "ERROR: lb build no generó la imagen ISO esperada." >&2
    exit 1
fi

cp "$GENERATED_ISO" "$OUTPUT_ISO"
cd "$OUTPUT_DIR"
sha256sum "$(basename "$OUTPUT_ISO")" > "$(basename "$OUTPUT_ISO").sha256"

echo "[LRP-ISO] ISO construida exitosamente en: $OUTPUT_ISO"
echo "[LRP-ISO] Sidecar SHA256 generado: ${OUTPUT_ISO}.sha256"
