#!/bin/bash
# build_whisper_avx1.sh — Build whisper.cpp for legacy AVX1 CPUs (e.g. Intel Ivy Bridge i5-3470)
# Flags strictly enable AVX/SSE4.2 and disable AVX2, FMA, and AVX512 to prevent SIGILL.
set -euo pipefail
export LC_ALL=C LANG=C

WHISPER_REPO="https://github.com/ggerganov/whisper.cpp.git"
WHISPER_TAG="v1.7.4"
BUILD_DIR="/tmp/whisper_cpp_avx1_build"
INSTALL_PREFIX="/usr/local"
MODELS_DIR="/var/lib/linuxremoteplayer/models"

MODE="dry-run"
DOWNLOAD_MODELS=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --build) MODE="build" ;;
        --dry-run) MODE="dry-run" ;;
        --download-models) DOWNLOAD_MODELS=1 ;;
        --models-dir) shift; MODELS_DIR="${1:-$MODELS_DIR}" ;;
        --prefix) shift; INSTALL_PREFIX="${1:-$INSTALL_PREFIX}" ;;
        --help|-h)
            echo "usage: build_whisper_avx1.sh [--dry-run|--build] [--download-models] [--models-dir DIR] [--prefix DIR]"
            exit 0
            ;;
        *)
            echo "Invalid argument: $1" >&2
            exit 1
            ;;
    esac
    shift
done

echo "=== LRP whisper.cpp AVX1 Toolchain ==="
echo "Target CPU Architecture: x86_64 AVX 1.0 (SSE4.2 + AVX; NO AVX2, NO FMA3)"
echo "Mode: $MODE"
echo "Install prefix: $INSTALL_PREFIX"
echo "Models directory: $MODELS_DIR"

# 1. Inspect host CPU capabilities if /proc/cpuinfo is present
if [ -f /proc/cpuinfo ]; then
    CPU_FLAGS=$(grep -m1 '^flags' /proc/cpuinfo || true)
    if echo "$CPU_FLAGS" | grep -qw "avx"; then
        echo "[OK] CPU flag 'avx' detected."
    else
        echo "[WARN] Host CPU does not declare 'avx' in /proc/cpuinfo."
    fi

    if echo "$CPU_FLAGS" | grep -qw "avx2"; then
        echo "[INFO] Host CPU supports AVX2, but build will strictly disable AVX2/FMA for appliance portability."
    else
        echo "[OK] Host CPU lacks AVX2; AVX1 build is required."
    fi
fi

CMAKE_FLAGS=(
    -DCMAKE_BUILD_TYPE=Release
    -DGGML_AVX=ON
    -DGGML_AVX2=OFF
    -DGGML_FMA=OFF
    -DGGML_AVX512=OFF
    -DGGML_CUDA=OFF
    -DWHISPER_BUILD_TESTS=OFF
    -DWHISPER_BUILD_EXAMPLES=ON
)

if [ "$MODE" = "dry-run" ]; then
    echo "[dry-run] Planned CMake configuration:"
    echo "  cmake -B build ${CMAKE_FLAGS[*]}"
    echo "  cmake --build build --config Release -j\$(nproc)"
    echo "  install build/bin/whisper-cli -> $INSTALL_PREFIX/bin/whisper-cli"
fi

if [ "$DOWNLOAD_MODELS" = 1 ]; then
    mkdir -p "$MODELS_DIR"
    BASE_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
    for model in "ggml-base-q5_0.bin" "ggml-small-q5_0.bin"; do
        dest="$MODELS_DIR/$model"
        if [ -f "$dest" ]; then
            echo "[OK] Model already present: $dest"
        else
            if [ "$MODE" = "dry-run" ]; then
                echo "[dry-run] Would download: $BASE_URL/$model -> $dest"
            else
                echo "[i] Downloading model $model..."
                curl -L -f -o "$dest.tmp" "$BASE_URL/$model"
                mv -f "$dest.tmp" "$dest"
                chmod 0644 "$dest"
                echo "[OK] Downloaded: $dest"
            fi
        fi
    done
fi

if [ "$MODE" = "build" ]; then
    # Ensure build dependencies
    if command -v apt-get >/dev/null 2>&1; then
        echo "[i] Checking build dependencies..."
        DEPS=()
        for cmd in cmake g++ git curl; do
            if ! command -v "$cmd" >/dev/null 2>&1; then
                case "$cmd" in
                    cmake) DEPS+=(cmake) ;;
                    g++) DEPS+=(build-essential) ;;
                    git) DEPS+=(git) ;;
                    curl) DEPS+=(curl) ;;
                esac
            fi
        done
        if [ ${#DEPS[@]} -gt 0 ]; then
            echo "[i] Installing missing build dependencies: ${DEPS[*]}"
            apt-get update && apt-get install -y "${DEPS[@]}"
        fi
    fi

    # Clone or update whisper.cpp
    mkdir -p "$(dirname "$BUILD_DIR")"
    if [ ! -d "$BUILD_DIR/.git" ]; then
        echo "[i] Cloning whisper.cpp ($WHISPER_TAG)..."
        rm -rf "$BUILD_DIR"
        git clone --branch "$WHISPER_TAG" --depth 1 "$WHISPER_REPO" "$BUILD_DIR"
    fi

    cd "$BUILD_DIR"

    # Configure CMake with strict AVX1 flags
    echo "[i] Configuring CMake with AVX1 (no AVX2/FMA)..."
    cmake -B build "${CMAKE_FLAGS[@]}"

    # Compile
    echo "[i] Compiling whisper.cpp..."
    NPROC=$(nproc 2>/dev/null || echo 2)
    cmake --build build --config Release -j"$NPROC"

    # Locate generated CLI executable
    CLI_BIN=""
    if [ -f "build/bin/whisper-cli" ]; then
        CLI_BIN="build/bin/whisper-cli"
    elif [ -f "build/bin/main" ]; then
        CLI_BIN="build/bin/main"
    fi

    if [ -z "$CLI_BIN" ]; then
        echo "[ERROR] whisper binary not found in build/bin/" >&2
        exit 1
    fi

    # Install binary
    mkdir -p "$INSTALL_PREFIX/bin"
    cp -f "$CLI_BIN" "$INSTALL_PREFIX/bin/whisper-cli"
    chmod 0755 "$INSTALL_PREFIX/bin/whisper-cli"
    echo "[OK] Installed $INSTALL_PREFIX/bin/whisper-cli"

    # Verify binary system info
    echo "[i] Verifying whisper-cli instruction set flags..."
    SYS_INFO=$("$INSTALL_PREFIX/bin/whisper-cli" --help 2>&1 | grep -i "system_info" || true)
    if [ -n "$SYS_INFO" ]; then
        echo "  $SYS_INFO"
        if echo "$SYS_INFO" | grep -q "AVX2 = 1"; then
            echo "[ERROR] AVX2 is enabled in binary! Build failed AVX1 compatibility gate." >&2
            exit 1
        fi
    fi
    echo "[SUCCESS] whisper.cpp AVX1 binary built and verified."
fi
