#!/usr/bin/env python3
"""benchmark_stt.py — Benchmark local speech-to-text with whisper.cpp AVX1.

Evaluates quantized models (e.g. ggml-base-q5_0 vs ggml-small-q5_0) on target CPU:
- Measures Real-Time Factor (RTF)
- Measures inference latency (ms)
- Measures peak RAM usage (RSS MB)
- Evaluates textual accuracy across canonical TV phrases
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Enforce UTF-8 for CLI stdout if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add backend directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import local_stt
from local_stt import WhisperRunner, generate_synthetic_pcm_wav, run_stt_benchmark

CANONICAL_PHRASES = [
    "abrir netflix",
    "pausar",
    "subir volumen",
    "buscar blade runner",
]


def prepare_phrase_audio(phrase: str, audio_dir: Path, mock: bool = False) -> bytes:
    """Generate or retrieve audio for a test phrase.
    
    If espeak-ng / ffmpeg is present, synthesizes realistic speech audio in memory.
    Otherwise, generates deterministic synthetic PCM WAV with prefix/suffix silence.
    """
    cached_file = audio_dir / f"{phrase.replace(' ', '_')}.wav"
    if cached_file.is_file():
        return cached_file.read_bytes()

    if not mock:
        # Attempt espeak-ng synthesis if available on Debian
        import shutil
        import subprocess
        espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        if espeak:
            cmd = [espeak, "-v", "es", "-s", "140", "--stdout", phrase]
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                # Normalize through local_stt transcode to 16kHz mono
                wav_16k = local_stt.transcode_to_pcm16k_mono(proc.stdout)
                audio_dir.mkdir(parents=True, exist_ok=True)
                cached_file.write_bytes(wav_16k)
                return wav_16k
            except Exception:
                pass

    # Deterministic synthetic audio fallback
    # Generate ~1.5s audio with tone + silence
    synth = generate_synthetic_pcm_wav(
        duration_s=1.2,
        freq_hz=400.0 + len(phrase) * 20.0,
        sample_rate=16000,
        prefix_silence_s=0.2,
        suffix_silence_s=0.2,
    )
    return synth


def main():
    parser = argparse.ArgumentParser(description="LRP Local STT AVX1 Benchmark")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["ggml-base-q5_0.bin", "ggml-small-q5_0.bin"],
        help="List of model filenames to benchmark",
    )
    parser.add_argument("--models-dir", default="/var/lib/linuxremoteplayer/models")
    parser.add_argument("--whisper-bin", default=None)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--mock", action="store_true", help="Simulate inference for CI/testing")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if args.mock:
        os.environ["LRP_STT_MOCK_RUNNER"] = "1"
        os.environ["LRP_MOCK_STT_TRANSCODE"] = "passthrough"

    runner = WhisperRunner(
        whisper_bin=args.whisper_bin,
        models_dir=args.models_dir,
        default_threads=args.threads,
    )

    audio_dir = Path("/tmp/lrp_stt_benchmark_audio")
    test_cases = []
    for phrase in CANONICAL_PHRASES:
        audio = prepare_phrase_audio(phrase, audio_dir, mock=args.mock)
        test_cases.append({"phrase": phrase, "audio": audio})

    results = run_stt_benchmark(runner, args.models, test_cases)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    print("\n=======================================================")
    print(" LRP Local STT Benchmark (AVX1 / Core i5-3470 Baseline)")
    print("=======================================================\n")

    for model, m_data in results["models"].items():
        print(f"### Modelo: {model}")
        print(f"- Latencia Promedio: {m_data['avg_latency_ms']} ms")
        print(f"- Real-Time Factor (RTF): {m_data['avg_rtf']}")
        print(f"- Acierto: {m_data['accuracy_pct']}% ({m_data['hits']}/{m_data['cases_count']})")
        print("\nDetalle por frase:")
        print("| Frase | Transcripción | Latencia (ms) | RTF | RAM (MB) | OK |")
        print("|---|---|---|---|---|---|")
        for c in m_data["cases"]:
            ok_str = "SÍ" if c.get("match") else "NO"
            print(
                f"| {c['phrase']} | {c.get('transcribed', '')} | "
                f"{c.get('latency_ms', 0)} | {c.get('rtf', 0)} | "
                f"{c.get('peak_rss_mb', 0)} | {ok_str} |"
            )
        print("\n" + "-" * 55 + "\n")

    print("### Resumen Comparativo")
    print("| Modelo | Latencia Promedio (ms) | RTF | Precisión (%) |")
    print("|---|---|---|---|")
    for s in results["summary"]:
        print(f"| {s['model']} | {s['avg_latency_ms']} | {s['avg_rtf']} | {s['accuracy_pct']}% |")
    print("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
