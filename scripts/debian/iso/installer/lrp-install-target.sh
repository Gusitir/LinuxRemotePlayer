#!/bin/bash
# ==============================================================================
# lrp-install-target.sh — LRP OS Automated Live-to-Disk Installer
# ==============================================================================
# Safely detects the fixed installation disk, strictly EXCLUDING the live boot
# USB media, partitions with GPT (LRP-BOOT EFI + LRP-ROOT ext4), configures
# zram swap, sets up the lrp user, LightDM autologin, and installs GRUB.
# ==============================================================================

set -euo pipefail

# Canonical partition labels
LABEL_BOOT="LRP-BOOT"
LABEL_ROOT="LRP-ROOT"
BOOT_SIZE_MIB="512"

# Colors for TTY output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[LRP-INSTALL]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[LRP-WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[LRP-ERROR]${NC} $*" >&2; }

usage() {
    cat <<EOF
Uso: $(basename "$0") [OPCIONES]

Instalador desatendido live-to-disk de LRP OS para HTPC.
Detecta de forma segura el almacenamiento fijo interno y excluye
estrictamente cualquier unidad USB o medio live activo.

Opciones:
  --target <DEVICE>   Fuerza el dispositivo de destino (ej. /dev/nvme0n1, /dev/sda).
                      Se valida estrictamente que NO sea USB ni el medio live.
  --dry-run           Simula la detección, particionado e instalación sin escribir en disco.
  --list-disks        Muestra el análisis y clasificación de discos del sistema y sale.
  --force-confirm     Omite la cuenta atrás de seguridad antes de formatear.
  -h, --help          Muestra esta ayuda.
EOF
}

# ------------------------------------------------------------------------------
# Detección del medio de arranque live activo
# ------------------------------------------------------------------------------
get_live_boot_device() {
    local live_dev=""
    
    # 1. Inspeccionar puntos de montaje live estándar de Debian/Live-boot
    for mnt in /run/live/medium /cdrom /live/image /run/live/rootfs/filesystem.squashfs /run/live/persistence; do
        if mountpoint -q "$mnt" 2>/dev/null; then
            live_dev=$(findmnt -n -o SOURCE "$mnt" 2>/dev/null || true)
            if [ -n "$live_dev" ]; then
                break
            fi
        fi
    done

    # 2. Si no se detectó por mountpoint, buscar por iso9660 o live-media en /proc/mounts
    if [ -z "$live_dev" ] && [ -f /proc/mounts ]; then
        live_dev=$(awk '$2 ~ /^\/(run\/live|live|cdrom)/ {print $1; exit}' /proc/mounts 2>/dev/null || true)
    fi

    # 3. Resolver dispositivo padre si live_dev es una partición (ej. /dev/sdb1 -> /dev/sdb)
    if [ -n "$live_dev" ] && [ -b "$live_dev" ]; then
        local parent
        parent=$(lsblk -n -o PKNAME "$live_dev" 2>/dev/null || true)
        if [ -n "$parent" ]; then
            echo "/dev/$parent"
            return 0
        fi
        echo "$live_dev"
        return 0
    fi

    echo ""
}

# ------------------------------------------------------------------------------
# Clasificación y filtrado seguro de discos
# ------------------------------------------------------------------------------
classify_disks() {
    local live_boot_dev="$1"

    if ! command -v lsblk >/dev/null 2>&1; then
        log_error "lsblk no está disponible en el sistema."
        return 1
    fi

    # Formato: NAME,TYPE,TRAN,RM,RO,SIZE,MODEL,VENDOR
    lsblk -d -n -b -P -o NAME,TYPE,TRAN,RM,RO,SIZE,MODEL,VENDOR | while read -r line; do
        eval "$line"

        # Filtrar solo dispositivos de tipo disk
        [ "${TYPE:-}" != "disk" ] && continue

        local dev_path="/dev/$NAME"
        local status="EXCLUDED"
        local reason=""

        # Exclusión 1: Dispositivo live desde el que se bootea (/run/live/medium, /cdrom, /live/image)
        if [ -n "$live_boot_dev" ] && [ "$dev_path" = "$live_boot_dev" ]; then
            reason="MEDIO_LIVE_ACTIVO"
        elif findmnt -n -o TARGET -S "$dev_path" 2>/dev/null | grep -E '^/(run/live/medium|cdrom|live/image)' >/dev/null 2>&1; then
            reason="MEDIO_LIVE_ACTIVO"
        # Exclusión 2: Transporte USB (/dev/disk/by-id/usb-* o TRAN=usb)
        elif [ "${TRAN:-}" = "usb" ]; then
            reason="TRANSPORTE_USB"
        # Exclusión 3: Dispositivos removibles (RM=1) salvo que sea NVMe/eMMC fijo
        elif [ "${RM:-0}" = "1" ] && [[ "$NAME" != nvme* ]] && [[ "$NAME" != mmcblk* ]]; then
            reason="REMOVIBLE"
        # Exclusión 4: Dispositivos de sólo lectura (RO=1)
        elif [ "${RO:-0}" = "1" ]; then
            reason="SOLO_LECTURA"
        # Exclusión 5: Dispositivos loop, zram, md, ram
        elif [[ "$NAME" == loop* ]] || [[ "$NAME" == zram* ]] || [[ "$NAME" == ram* ]] || [[ "$NAME" == sr* ]]; then
            reason="VIRTUAL_O_OPTICO"
        # Exclusión 6: Menor a 8 GB (improbable disco de sistema para appliance HTPC)
        elif [ "${SIZE:-0}" -lt 8589934592 ]; then
            reason="CAPACIDAD_INSUFICIENTE_<8GB"
        else
            status="CANDIDATO_FIJO"
            reason="DISCO_INTERNO_VALIDO"
        fi

        local size_gb
        size_gb=$(awk "BEGIN {printf \"%.1f GB\", ${SIZE:-0} / 1073741824}")
        echo "${dev_path}|${status}|${reason}|${size_gb}|${MODEL:-Desconocido}|${VENDOR:-}"
    done
}

# ------------------------------------------------------------------------------
# Selección del disco destino óptimo
# ------------------------------------------------------------------------------
select_target_disk() {
    local requested_target="$1"
    local live_boot_dev
    live_boot_dev=$(get_live_boot_device)

    local classified
    classified=$(classify_disks "$live_boot_dev")

    # Si se solicitó un disco explícito, validarlo estrictamente
    if [ -n "$requested_target" ]; then
        local match
        match=$(echo "$classified" | grep "^${requested_target}|" || true)
        if [ -z "$match" ]; then
            log_error "El disco solicitado '$requested_target' no fue detectado por el kernel."
            return 1
        fi
        local status reason
        status=$(echo "$match" | cut -d'|' -f2)
        reason=$(echo "$match" | cut -d'|' -f3)
        if [ "$status" != "CANDIDATO_FIJO" ]; then
            log_error "SEGURIDAD: El disco solicitado '$requested_target' fue RECHAZADO: $reason."
            log_error "No se permite instalar sobre medios USB o dispositivos no aptos."
            return 1
        fi
        echo "$requested_target"
        return 0
    fi

    # Auto-selección: Filtrar candidatos válidos
    local candidates
    candidates=$(echo "$classified" | grep "|CANDIDATO_FIJO|" || true)
    local count
    count=$(echo "$candidates" | grep -c "^/dev/" || true)

    if [ "$count" -eq 0 ]; then
        log_error "CRÍTICO: No se encontró ningún disco fijo apto para la instalación de LRP OS."
        log_error "Unidades USB y medios activos fueron excluidos por salvaguarda de seguridad."
        return 1
    fi

    # Prioridad: NVMe SSD > SATA SSD/HDD
    local selected=""
    local nvme_cand
    nvme_cand=$(echo "$candidates" | grep "^/dev/nvme" | head -n1 | cut -d'|' -f1 || true)
    if [ -n "$nvme_cand" ]; then
        selected="$nvme_cand"
    else
        # Tomar el primer candidato fijo (ej. /dev/sda)
        selected=$(echo "$candidates" | head -n1 | cut -d'|' -f1)
    fi

    echo "$selected"
}

# ------------------------------------------------------------------------------
# Helpers de particionado GPT
# ------------------------------------------------------------------------------
get_partition_path() {
    local disk="$1"
    local part_num="$2"
    if [[ "$disk" =~ [0-9]$ ]]; then
        echo "${disk}p${part_num}"
    else
        echo "${disk}${part_num}"
    fi
}

partition_and_format() {
    local target_disk="$1"
    local dry_run="$2"

    local boot_part
    local root_part
    boot_part=$(get_partition_path "$target_disk" 1)
    root_part=$(get_partition_path "$target_disk" 2)

    log_info "Dispositivo de destino: $target_disk"
    log_info "Partición 1 (EFI / Boot): $boot_part (512 MiB, FAT32, LABEL=$LABEL_BOOT)"
    log_info "Partición 2 (Root ext4):   $root_part (Resto, ext4, LABEL=$LABEL_ROOT)"

    if [ "$dry_run" = "true" ]; then
        log_info "[DRY-RUN] Simulando particionado y formateo sin tocar almacenamiento físico."
        echo "DRY_RUN_OK"
        return 0
    fi

    # Desmontar particiones existentes en el disco si estuvieran montadas
    for p in $(lsblk -n -o PATH "$target_disk" 2>/dev/null | tail -n +2); do
        umount "$p" 2>/dev/null || true
    done

    # Limpieza de tablas de particiones existentes
    log_info "Limpiando firmas previas con wipefs y sgdisk..."
    wipefs -a -f "$target_disk"
    if command -v sgdisk >/dev/null 2>&1; then
        sgdisk --zap-all "$target_disk"
        partprobe "$target_disk" 2>/dev/null || sleep 1

        # Crear esquema GPT:
        # Part 1: EFI System Partition (+512M, type EF00)
        # Part 2: Linux filesystem (Resto, type 8300)
        sgdisk -n "1:2048:+${BOOT_SIZE_MIB}M" -t 1:EF00 -c 1:"$LABEL_BOOT" "$target_disk"
        sgdisk -n "2:0:0" -t 2:8300 -c 2:"$LABEL_ROOT" "$target_disk"
        partprobe "$target_disk" 2>/dev/null || sleep 1
    elif command -v parted >/dev/null 2>&1; then
        parted -s "$target_disk" mklabel gpt
        parted -s "$target_disk" mkpart "$LABEL_BOOT" fat32 1MiB 513MiB
        parted -s "$target_disk" set 1 esp on
        parted -s "$target_disk" mkpart "$LABEL_ROOT" ext4 513MiB 100%
        partprobe "$target_disk" 2>/dev/null || sleep 1
    else
        log_error "Ni sgdisk ni parted están presentes para crear la tabla de particiones."
        return 1
    fi

    # Esperar a que el kernel registre los nodos de dispositivo
    udevadm settle 2>/dev/null || sleep 2

    # Formateo
    log_info "Formateando $boot_part como VFAT32 ($LABEL_BOOT)..."
    mkfs.vfat -F 32 -n "$LABEL_BOOT" "$boot_part"

    log_info "Formateando $root_part como ext4 ($LABEL_ROOT)..."
    mkfs.ext4 -F -L "$LABEL_ROOT" "$root_part"

    log_info "Particionado y formateo completados exitosamente."
}

# ------------------------------------------------------------------------------
# Copia del sistema live al disco e instalación de bootloader
# ------------------------------------------------------------------------------
install_payload() {
    local target_disk="$1"
    local dry_run="$2"

    local boot_part
    local root_part
    boot_part=$(get_partition_path "$target_disk" 1)
    root_part=$(get_partition_path "$target_disk" 2)
    local target_mnt="/target"

    if [ "$dry_run" = "true" ]; then
        log_info "[DRY-RUN] Simulación de instalación y despliegue del sistema completada."
        return 0
    fi

    mkdir -p "$target_mnt"
    mount "$root_part" "$target_mnt"
    mkdir -p "$target_mnt/boot/efi"
    mount "$boot_part" "$target_mnt/boot/efi"

    log_info "Sincronizando sistema operativo base a $target_mnt..."
    # rsync devuelve 23/24 por archivos que desaparecen o sin permiso en un live;
    # con set -e eso abortaba la instalacion ANTES de instalar GRUB y dejaba el
    # disco sin cargador. Solo 0/23/24 se consideran validos.
    local rsync_rc=0
    rsync -aHAX --delete \
        --exclude='/target' \
        --exclude='/proc/*' \
        --exclude='/sys/*' \
        --exclude='/dev/*' \
        --exclude='/run/*' \
        --exclude='/tmp/*' \
        --exclude='/mnt/*' \
        --exclude='/media/*' \
        --exclude='/lost+found' \
        --exclude='/var/log/*' \
        --exclude='/var/cache/*' \
        --exclude='/etc/mtab' \
        / "$target_mnt/" || rsync_rc=$?
    if [ "$rsync_rc" -ne 0 ] && [ "$rsync_rc" -ne 23 ] && [ "$rsync_rc" -ne 24 ]; then
        log_error "rsync fallo con codigo $rsync_rc; abortando antes de tocar el bootloader."
        return 1
    fi
    log_info "Rsync completado (codigo $rsync_rc)."
    mkdir -p "$target_mnt/boot/grub" "$target_mnt/boot/efi" "$target_mnt/var/lib/linuxremoteplayer"

    # Generar fstab canónico usando etiquetas de partición
    log_info "Configurando /etc/fstab canónico..."
    cat <<EOF > "$target_mnt/etc/fstab"
# /etc/fstab — LRP OS Appliance canónico
LABEL=$LABEL_ROOT  /          ext4  defaults,noatime,discard  0 1
LABEL=$LABEL_BOOT  /boot/efi   vfat  umask=0077                0 2
tmpfs              /tmp       tmpfs defaults,nosuid,nodev     0 0
EOF

    # Configuración de swap zram con zstd
    log_info "Configurando swap zram zstd para hardware modesto..."
    mkdir -p "$target_mnt/etc/systemd"
    cat <<EOF > "$target_mnt/etc/systemd/zram-generator.conf"
[zram0]
zram-size = min(ram / 2, 4096)
compression-algorithm = zstd
swap-priority = 100
fs-type = swap
EOF

    # Configuración de GRUB en chroot
    mkdir -p "$target_mnt/var/log" "$target_mnt/boot/grub" "$target_mnt/boot/efi"
    log_info "Instalando bootloader GRUB en $target_disk..."
    for fs in proc sys dev dev/pts; do
        mount --bind "/$fs" "$target_mnt/$fs"
    done

    # Instalar GRUB firmado para Secure Boot: shim + grub-efi-amd64-signed.
    # --removable evita depender de NVRAM (efibootmgr no siempre funciona en live)
    # y garantiza BOOTX64.EFI incluso si el firmware ignora la NVRAM.
    log_info "Instalando GRUB EFI firmado (shim + fallback BOOTX64.EFI)..."
    # A) Entrada NVRAM normal: aparece "LRP-OS" en el menu de arranque del firmware.
    chroot "$target_mnt" grub-install \
        --target=x86_64-efi \
        --efi-directory=/boot/efi \
        --bootloader-id=LRP-OS \
        --uefi-secure-boot \
        --recheck >>"$target_mnt/var/log/lrp-install-grub.log" 2>&1 || \
        log_warn "Entrada NVRAM no escrita (normal en live); se usara el fallback."
    # B) Fallback removible: arranca aunque el firmware ignore la NVRAM.
    if ! chroot "$target_mnt" grub-install \
            --target=x86_64-efi \
            --efi-directory=/boot/efi \
            --bootloader-id=LRP-OS \
            --uefi-secure-boot \
            --removable --no-nvram --recheck >>"$target_mnt/var/log/lrp-install-grub.log" 2>&1; then
        log_error "grub-install EFI firmado fallo; probando sin shim."
        chroot "$target_mnt" grub-install \
            --target=x86_64-efi \
            --efi-directory=/boot/efi \
            --bootloader-id=LRP-OS \
            --removable --no-nvram --recheck >>"$target_mnt/var/log/lrp-install-grub.log" 2>&1 || true
    fi
    mkdir -p "$target_mnt/boot/efi/EFI/BOOT"
    if [ -f "$target_mnt/boot/efi/EFI/BOOT/BOOTX64.EFI" ]; then
        log_info "Fallback EFI presente: EFI/BOOT/BOOTX64.EFI"
    else
        log_error "Sin BOOTX64.EFI: el firmware podria no arrancar el disco."
    fi

    # C) Entrada NVRAM propia y primera en BootOrder: evita que el firmware
    # caiga en la entrada legacy "Hard Drive" (que no tiene GRUB BIOS y no arranca).
    local nvram_result="skipped(no-uefi)"
    if [ -d /sys/firmware/efi ] && command -v efibootmgr >/dev/null 2>&1; then
        local esp_num efi_rel nvram_num
        esp_num=$(printf '%s' "$boot_part" | sed -n 's/.*[^0-9]\([0-9][0-9]*\)$/\1/p')
        efi_rel='\EFI\BOOT\BOOTX64.EFI'
        [ -f "$target_mnt/boot/efi/EFI/LRP-OS/shimx64.efi" ] && efi_rel='\EFI\LRP-OS\shimx64.efi'
        if efibootmgr -c -d "$target_disk" -p "${esp_num:-1}" -L "LRP-OS" -l "$efi_rel" \
                >>"$target_mnt/var/log/lrp-install-grub.log" 2>&1; then
            nvram_result="created"
            nvram_num=$(efibootmgr 2>/dev/null | sed -n 's/^Boot\([0-9A-Fa-f]\{4\}\)\* LRP-OS.*/\1/p' | head -1)
            if [ -n "$nvram_num" ]; then
                local rest_order
                rest_order=$(efibootmgr 2>/dev/null | sed -n 's/^BootOrder: //p' | tr ',' '\n' \
                    | grep -v "^${nvram_num}$" | paste -sd, - || true)
                if efibootmgr -o "${nvram_num}${rest_order:+,$rest_order}" \
                        >>"$target_mnt/var/log/lrp-install-grub.log" 2>&1; then
                    nvram_result="created+first"
                fi
            fi
            log_info "Entrada NVRAM LRP-OS (${nvram_result}) sobre ${efi_rel}."
        else
            nvram_result="failed"
            log_warn "efibootmgr no pudo crear la entrada; el firmware usara el fallback EFI/BOOT."
        fi
    fi

    # BIOS/i386-pc solo tiene sentido si el live arranco en legacy. En UEFI el
    # install sobre GPT sin particion BIOS Boot falla por diseño (blocklists).
    local bios_grub="skipped(uefi)"
    if [ ! -d /sys/firmware/efi ]; then
        log_info "Instalando GRUB BIOS (i386-pc)..."
        if chroot "$target_mnt" grub-install --target=i386-pc "$target_disk" --recheck \
                >>"$target_mnt/var/log/lrp-install-grub.log" 2>&1; then
            bios_grub="ok"
        else
            bios_grub="failed"
            log_warn "grub-install BIOS fallo; el disco solo arrancara en modo UEFI."
        fi
    fi

    chroot "$target_mnt" update-grub >>"$target_mnt/var/log/lrp-install-grub.log" 2>&1 || \
        log_error "update-grub fallo; revisar /var/log/lrp-install-grub.log"

    if [ -f "$target_mnt/boot/grub/grub.cfg" ]; then
        log_info "grub.cfg generado en el destino."
    else
        log_error "No se genero grub.cfg en el destino."
    fi

    # Reporte persistente y visible en consola para diagnosticar sin arrancar el disco.
    {
        echo "LRP OS install report $(date -Is)"
        echo "target=$target_disk root=$root_part boot=$boot_part"
        echo "live_boot_mode: $([ -d /sys/firmware/efi ] && echo uefi || echo legacy)"
        echo "rsync_rc=$rsync_rc"
        echo "esp:"; find "$target_mnt/boot/efi" -maxdepth 3 -type f | sed "s|$target_mnt||"
        echo "grub_cfg: $([ -f "$target_mnt/boot/grub/grub.cfg" ] && echo yes || echo no)"
        echo "secure_boot_efi: $([ -f "$target_mnt/boot/efi/EFI/BOOT/BOOTX64.EFI" ] && echo yes || echo no)"
        echo "nvram_entry: ${nvram_result:-skipped}"
        echo "bios_grub: ${bios_grub:-skipped}"
        echo "hosts: $([ -s "$target_mnt/etc/hosts" ] && echo yes || echo EMPTY)"
    } | tee "$target_mnt/var/log/lrp-install-report.txt" | tee /run/lrp-install-report.txt >&2

    # Desmontar recursos
    for fs in dev/pts dev sys proc boot/efi; do
        umount "$target_mnt/$fs" 2>/dev/null || true
    done
    umount "$target_mnt" 2>/dev/null || true

    log_info "Instalación de LRP OS completada con éxito."
}

# ------------------------------------------------------------------------------
# B40: aviso final y reinicio automatico SOLO en modo desatendido
# ------------------------------------------------------------------------------
finish_install() {
    local force_confirm="$1"
    local dry_run="$2"

    echo "Instalación completa. Retirá el USB y reiniciá para arrancar desde el disco."

    # Auto-install: servicio lrp-auto-install (systemd) o --force-confirm sin TTY.
    local auto_install="false"
    if [ -n "${INVOCATION_ID:-}" ] || { [ "$force_confirm" = "true" ] && [ ! -t 0 ]; }; then
        auto_install="true"
    fi
    if [ "$dry_run" != "false" ] || [ "$auto_install" != "true" ]; then
        return 0
    fi

    local remaining=15
    while [ "$remaining" -gt 0 ]; do
        if [ -t 0 ]; then
            printf '\rReiniciando en %ss (pulsá una tecla para cancelar)... ' "$remaining"
            if read -r -t 1 -n 1 _; then
                printf '\n'
                log_info "Reinicio cancelado. Retirá el USB y reiniciá manualmente."
                return 0
            fi
        else
            echo "Reiniciando en ${remaining}s..."
            sleep 1
        fi
        remaining=$((remaining - 1))
    done
    printf '\n'
    log_info "Reiniciando para arrancar desde el disco..."
    systemctl reboot || log_warn "No se pudo reiniciar automáticamente; reiniciá manualmente."
}

# ------------------------------------------------------------------------------
# Entrypoint principal
# ------------------------------------------------------------------------------
main() {
    local target_disk=""
    local dry_run="false"
    local list_disks="false"
    local force_confirm="false"

    while [ $# -gt 0 ]; do
        case "$1" in
            --target)
                target_disk="$2"
                shift 2
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            --list-disks)
                list_disks="true"
                shift
                ;;
            --force-confirm)
                force_confirm="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                usage
                exit 1
                ;;
        esac
    done

    local live_dev
    live_dev=$(get_live_boot_device)
    log_info "Medio de arranque live detectado: ${live_dev:-Ninguno (ejecución estándar)}"

    if [ "$list_disks" = "true" ]; then
        log_info "Clasificación de dispositivos de almacenamiento detectados:"
        echo -e "DISPOSITIVO\tESTADO\t\tMOTIVO\t\t\tTAMAÑO\tMODELO"
        classify_disks "$live_dev" | tr '|' '\t'
        exit 0
    fi

    local selected_target
    selected_target=$(select_target_disk "$target_disk") || exit 1
    log_info "Disco destino seleccionado: $selected_target"

    # Estado del firmware: decide shim firmado (UEFI+SB) o MBR BIOS.
    if [ -d /sys/firmware/efi ]; then
        local sb_val=0
        local sb_file=/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c
        if [ -r "$sb_file" ]; then
            sb_val=$(od -An -t u1 "$sb_file" | awk '{print $NF}')
        fi
        if [ "${sb_val:-0}" = "1" ]; then
            log_warn "Firmware UEFI con Secure Boot ACTIVO: se instalara shim + GRUB firmado."
        else
            log_info "Firmware UEFI detectado (Secure Boot desactivado)."
        fi
    else
        log_warn "Firmware BIOS/legacy detectado: se instalara GRUB i386-pc en el MBR."
    fi

    if [ "$dry_run" = "false" ] && [ "$force_confirm" = "false" ]; then
        log_warn "ADVERTENCIA: Se formateará por completo el disco $selected_target."
        log_warn "Todos los datos existentes serán eliminados permanentemente."
        echo -n "Presiona CTRL+C para cancelar o espera 5 segundos para continuar..."
        sleep 5
        echo ""
    fi

    partition_and_format "$selected_target" "$dry_run"
    install_payload "$selected_target" "$dry_run"

    log_info "Operación finalizada. Ya puedes retirar el USB y reiniciar el HTPC."
    finish_install "$force_confirm" "$dry_run"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    main "$@"
fi
