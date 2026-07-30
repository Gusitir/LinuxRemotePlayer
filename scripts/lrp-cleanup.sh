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

# 5. Borrar el .env. VA ULTIMO A PROPOSITO: el paso 1 lo lee para sacar el LICENSE_TOKEN
#    y liberar la licencia en el servidor. Si se borrara antes, la licencia quedaria
#    ocupada para siempre y el usuario perderia su slot.
#    Se borra porque guarda DOS credenciales -- LICENSE_TOKEN y PAIRING_TOKEN -- y una
#    desinstalacion no puede dejarlas en el disco. Ademas, mientras el token siguiera ahi,
#    una reinstalacion re-reclamaba la licencia sola.
rm -f "$BACKEND_DIR/.env" 2>/dev/null

echo "[+] LRP: limpieza completada."
exit 0
