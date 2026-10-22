"""Unit and mock tests for local Speech-to-Text (STT) infrastructure.

Verifies:
1. In-memory WAV generation and PCM 16kHz parsing.
2. Voice Activity Detection (VAD) energy thresholding and silence trimming.
3. In-memory transcoding pipeline error handling and mock hooks.
4. Whisper.cpp AVX1 runner integration, metrics calculation (RTF, RSS, latency), and transcription cleaning.
5. Comparative benchmark runner execution without physical hardware dependencies.
"""
import os
import sys
import io
import wave
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import local_stt
from local_stt import (
    generate_synthetic_pcm_wav,
    transcode_to_pcm16k_mono,
    process_vad_and_silence,
    WhisperRunner,
    run_stt_benchmark,
)


def test_synthetic_wav_generation_properties():
    """Verify that synthetic WAV generator produces valid 16kHz mono 16-bit PCM."""
    wav_bytes = generate_synthetic_pcm_wav(
        duration_s=0.5,
        freq_hz=440.0,
        sample_rate=16000,
        prefix_silence_s=0.1,
        suffix_silence_s=0.1,
    )
    assert wav_bytes.startswith(b"RIFF")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 16000
        # Total duration = 0.1 + 0.5 + 0.1 = 0.7s -> ~11200 frames
        assert wf.getnframes() == pytest.approx(11200, abs=50)


def test_transcode_fast_path_and_validation():
    """Verify in-memory transcoding fast-path, empty buffer guard, and mock mode."""
    # 1. Empty buffer raises ValueError
    with pytest.raises(ValueError, match="Empty audio buffer"):
        transcode_to_pcm16k_mono(b"")

    # 2. Pre-formatted 16kHz mono WAV passes through without ffmpeg
    valid_wav = generate_synthetic_pcm_wav(duration_s=0.2)
    result = transcode_to_pcm16k_mono(valid_wav)
    assert result == valid_wav

    # 3. Mock transcode error override
    os.environ["LRP_MOCK_STT_TRANSCODE"] = "error"
    try:
        with pytest.raises(RuntimeError, match="Mock transcoding failure"):
            transcode_to_pcm16k_mono(b"dummy audio")
    finally:
        del os.environ["LRP_MOCK_STT_TRANSCODE"]


def test_vad_pure_silence_rejection():
    """VAD must detect pure silence and reject without executing speech inference."""
    # 1.0 second of pure digital silence
    silent_wav = generate_synthetic_pcm_wav(
        duration_s=1.0,
        amplitude=0,  # Zero amplitude
    )
    has_speech, trimmed_bytes, meta = process_vad_and_silence(
        silent_wav, threshold_rms=200.0
    )
    assert has_speech is False
    assert trimmed_bytes == b""
    assert meta["reason"] == "no_speech"
    assert meta["avg_rms"] == 0.0
    assert meta["speech_ratio"] == 0.0


def test_vad_silence_trimming():
    """VAD must detect speech burst and trim surrounding leading and trailing silence."""
    # 0.4s silence + 0.6s tone + 0.4s silence (total 1.4s)
    audio_wav = generate_synthetic_pcm_wav(
        duration_s=0.6,
        freq_hz=500.0,
        amplitude=15000,
        prefix_silence_s=0.4,
        suffix_silence_s=0.4,
    )
    has_speech, trimmed_bytes, meta = process_vad_and_silence(
        audio_wav, threshold_rms=200.0, frame_duration_ms=30, padding_ms=90
    )
    assert has_speech is True
    assert len(trimmed_bytes) > 0
    assert meta["is_speech"] is True
    assert meta["original_duration_s"] == pytest.approx(1.4, abs=0.05)
    # Trimmed duration should be ~0.6s speech + ~0.18s padding = ~0.78s (< 1.4s)
    assert meta["trimmed_duration_s"] < meta["original_duration_s"]
    assert meta["trimmed_ms"] > 200.0

    # Verify trimmed bytes are valid WAV
    with wave.open(io.BytesIO(trimmed_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == 16000
        assert wf.getnframes() > 0


def test_vad_malformed_and_edge_cases():
    """VAD gracefully handles corrupt bytes, non-RIFF data, and unsupported formats."""
    # Corrupt data
    has_speech, _, meta = process_vad_and_silence(b"not a wav file")
    assert has_speech is False
    assert meta["reason"] == "invalid_wav"

    # Empty bytes
    has_speech, _, meta = process_vad_and_silence(b"")
    assert has_speech is False
    assert meta["reason"] == "invalid_wav"


def test_whisper_runner_text_cleaning():
    """Whisper output text cleaning strips timestamps, punctuation, and lowercases."""
    raw_output = """
    [00:00:00.000 --> 00:00:01.500]  ¡Abrir Netflix!
    [00:00:01.500 --> 00:00:02.000]  
    """
    clean = WhisperRunner._clean_transcription(raw_output)
    assert clean == "abrir netflix"

    # Multiple lines without timestamps
    multi_line = "  ¿Pausar? \n  Por favor. "
    clean_multi = WhisperRunner._clean_transcription(multi_line)
    assert clean_multi == "pausar por favor"


def test_whisper_runner_mock_transcription(monkeypatch):
    """WhisperRunner executes end-to-end in mock mode with RTF and RSS calculation."""
    audio_wav = generate_synthetic_pcm_wav(
        duration_s=1.0,
        freq_hz=440.0,
        amplitude=12000,
        prefix_silence_s=0.1,
    )

    runner = WhisperRunner(models_dir="/tmp/lrp_mock_models")
    monkeypatch.setenv("LRP_STT_MOCK_RUNNER", "1")
    monkeypatch.setenv("LRP_STT_MOCK_TEXT", "subir volumen")

    res = runner.transcribe(audio_wav, model_name="ggml-base-q5_0.bin")
    assert res["ok"] is True
    assert res["text"] == "subir volumen"
    assert res["model"] == "ggml-base-q5_0.bin"
    assert res["latency_ms"] > 0
    assert res["rtf"] > 0
    assert res["peak_rss_mb"] > 0
    assert "vad" in res


def test_whisper_runner_missing_binary_and_model(tmp_path):
    """WhisperRunner reports clean error reasons when binary or model file is missing."""
    audio_wav = generate_synthetic_pcm_wav(duration_s=0.5, amplitude=12000)

    # 1. Missing binary
    runner_no_bin = WhisperRunner(whisper_bin="/nonexistent/whisper-cli", models_dir=str(tmp_path))
    res = runner_no_bin.transcribe(audio_wav, model_name="ggml-base-q5_0.bin")
    assert res["ok"] is False
    assert res["reason"] == "whisper_bin_missing"

    # 2. Binary exists (mocked dummy executable) but model missing
    dummy_bin = tmp_path / "mock-whisper-cli"
    dummy_bin.write_text("#!/bin/sh\nexit 0\n")
    dummy_bin.chmod(0o755)

    runner_no_model = WhisperRunner(whisper_bin=str(dummy_bin), models_dir=str(tmp_path))
    res = runner_no_model.transcribe(audio_wav, model_name="ggml-base-q5_0.bin")
    assert res["ok"] is False
    assert "model_missing" in res["reason"]


def test_stt_benchmark_harness_mock(monkeypatch):
    """Test full comparative benchmark harness execution across canonical TV phrases."""
    monkeypatch.setenv("LRP_STT_MOCK_RUNNER", "1")
    runner = WhisperRunner(models_dir="/tmp/lrp_models")

    test_cases = [
        {"phrase": "abrir netflix", "audio": generate_synthetic_pcm_wav(duration_s=0.8, amplitude=12000)},
        {"phrase": "pausar", "audio": generate_synthetic_pcm_wav(duration_s=0.5, amplitude=12000)},
        {"phrase": "subir volumen", "audio": generate_synthetic_pcm_wav(duration_s=0.7, amplitude=12000)},
        {"phrase": "buscar blade runner", "audio": generate_synthetic_pcm_wav(duration_s=0.9, amplitude=12000)},
    ]

    models = ["ggml-base-q5_0.bin", "ggml-small-q5_0.bin"]
    results = run_stt_benchmark(runner, models, test_cases)

    assert "models" in results
    assert "summary" in results
    assert len(results["summary"]) == 2
    for s in results["summary"]:
        assert s["model"] in models
        assert s["avg_latency_ms"] > 0
        assert s["avg_rtf"] > 0
        assert 0.0 <= s["accuracy_pct"] <= 100.0
