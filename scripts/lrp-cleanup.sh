#!/bin/bash
# Limpieza de sistema de LinuxRemotePlayer. NO INTERACTIVO.
# Lo llaman: DEBIAN/prerm (SOLO en remove) y scripts/uninstall.sh.
# REGLAS DE ORO DE ESTE ARCHIVO: sin `set -e`, cada comando tolerado, y SIEMPRE
# `exit 0`. Un fallo aca JAMAS puede abortar un `apt remove` ni dejar el paquete
# a medio desinstalar. Es preferible no limpiar algo a romper la desinstalacion.

BACKEND_DIR="${LRP_BACKEND_DIR:-/opt/linuxremoteplayer/backend}"

echo "[i] LRP: limpieza del sistema..."

# 1. Liberar la licencia de ESTE dispositivo (best-effort). Timeout corto a
#    proposito: una red caida no puede colgar un apt remove.
if [ -f "$BACKEND_DIR/.env" ] && [ -f /etc/machine-id ]; then
    LIC_TOKEN=$(grep -E '^LICENSE_TOKEN=' "$BACKEND_DIR/.env" | head -n1 | cut -d= -f2- | tr -d "'\"")
    PROXY_URL=$(grep -E '^AI_PROXY_URL=' "$BACKEND_DIR/.env" | head -n1 | cut -d= -f2- | tr -d "'\"")
    PROXY_URL=${PROXY_URL:-https://tbijfdbtauzxbsbkujbs.functions.supabase.co/ai-proxy}
    if [ -n "$LIC_TOKEN" ]; then
        DEVICE_ID=$(tr -d '[:space:]' < /etc/machine-id | sha256sum | awk '{print $1}')
        curl -s -m 5 -X POST "$PROXY_URL" \
             -H "Content-Type: application/json" \
             -d "{\"action\":\"release\",\"token\":\"$LIC_TOKEN\",\"device_id\":\"$DEVICE_ID\"}" >/dev/null 2>&1
        echo "[+] LRP: liberacion de licencia intentada."
    fi
fi

# 2. Reglas udev de uinput
rm -f /etc/udev/rules.d/99-uinput.rules 2>/dev/null
rm -f /etc/modules-load.d/uinput.conf 2>/dev/null
udevadm control --reload-rules >/dev/null 2>&1
udevadm trigger >/dev/null 2>&1

# 3. Regla del firewall
if command -v ufw >/dev/null 2>&1; then
    ufw delete allow 8000/tcp >/dev/null 2>&1
fi

# 4. Devolver la suspension del sistema (install.sh la enmascara con LRP_NOSLEEP)
systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target >/dev/null 2>&1

# 5. Borrar todo lo que se genero en tiempo de ejecucion.
#    VA ULTIMO A PROPOSITO: el paso 1 lee el .env para sacar el LICENSE_TOKEN y liberar la
#    licencia en el servidor. Si se borrara antes, la licencia quedaria ocupada para siempre
#    y el usuario perderia su slot de dispositivo.
#
#    Que se lleva y por que:
#      .env            -> el LICENSE_TOKEN. Mientras siguiera ahi, una reinstalacion
#                         re-reclamaba la licencia sola y no se podia probar la mudanza.
#      .pairing_token  -> la credencial de emparejamiento. OJO: NO vive en el .env, aunque
#                         el comentario viejo de este script decia lo contrario. auth.py la
#                         lee de este archivo (lo escribe install.sh), asi que borrar solo
#                         el .env la dejaba intacta.
#      certs/          -> incluye ca.key y key.pem, o sea CLAVES PRIVADAS. Hasta 1.8.11 solo
#                         las borraba uninstall.sh, asi que `apt remove` -- el camino que
#                         recomienda la documentacion -- las dejaba en el disco.
rm -f "$BACKEND_DIR/.env" 2>/dev/null
rm -f "$BACKEND_DIR/.pairing_token" 2>/dev/null
rm -rf "$BACKEND_DIR/certs" 2>/dev/null

# 6. Sacar la CA del almacen de confianza del sistema. install.sh la instala ahi y ningun
#    script la quitaba: quedaba una autoridad certificadora de confianza instalada despues
#    de desinstalar el producto.
if [ -f /usr/local/share/ca-certificates/lrp-ca.crt ]; then
    rm -f /usr/local/share/ca-certificates/lrp-ca.crt 2>/dev/null
    update-ca-certificates --fresh >/dev/null 2>&1
fi

echo "[+] LRP: limpieza completada."
exit 0
