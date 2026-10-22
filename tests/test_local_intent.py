"""Deterministic unit tests for local NLU intent engine and offline voice pipeline.

Verifies:
1. Canonical intent parsing across allowlisted categories (launch_kiosk, media_control, search, system_control).
2. Whisper phonetic alias and misspelling normalization (e.g. posar, blader anero, yutup).
3. Compound app + query extraction.
4. Security guardrails and absolute rejection of shell metacharacters and injections.
5. Strict execution latency bounds (<50ms on CPU).
6. Complete offline voice_command integration in ai_pipeline without Supabase / license dependency.
"""
import os
import sys
import time
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import local_intent
from local_intent import (
    parse_intent,
    sanitize_input,
    ALLOWED_MEDIA_KEYS,
    DEFAULT_VALID_TARGETS,
    ALLOWED_SYSTEM_COMMANDS,
)
import ai_pipeline


def test_canonical_media_control():
    """Verify standard media commands map to strictly allowlisted Linux input keys."""
    test_cases = [
        ("pausar", "KEY_PLAYPAUSE"),
        ("pausa", "KEY_PLAYPAUSE"),
        ("reproducir", "KEY_PLAYPAUSE"),
        ("reanudar", "KEY_PLAYPAUSE"),
        ("dale play", "KEY_PLAYPAUSE"),
        ("subir volumen", "KEY_VOLUMEUP"),
        ("sube el volumen", "KEY_VOLUMEUP"),
        ("mas volumen", "KEY_VOLUMEUP"),
        ("bajar volumen", "KEY_VOLUMEDOWN"),
        ("baja el volumen", "KEY_VOLUMEDOWN"),
        ("menos volumen", "KEY_VOLUMEDOWN"),
        ("silenciar", "KEY_MUTE"),
        ("mutear", "KEY_MUTE"),
        ("siguiente", "KEY_NEXTSONG"),
        ("anterior", "KEY_PREVIOUSSONG"),
    ]
    for text, expected_key in test_cases:
        res = parse_intent(text)
        assert res["action"] == "media_control", f"Failed for {text}"
        assert res["parameters"]["key"] == expected_key
        assert expected_key in ALLOWED_MEDIA_KEYS
        assert res["latency_ms"] < 50.0


def test_canonical_app_launch():
    """Verify application launch intents against registered kiosk targets."""
    test_cases = [
        ("abrir netflix", "netflix"),
        ("iniciar youtube", "youtube"),
        ("poner spotify", "spotify"),
        ("ir a prime video", "primevideo"),
        ("abrir disney plus", "disney"),
        ("abrir hbo max", "hbomax"),
        ("crunchyroll", "crunchyroll"),
        ("abrir twitch", "twitch"),
        ("stremio", "stremio"),
    ]
    for text, expected_app in test_cases:
        res = parse_intent(text)
        assert res["action"] == "launch_kiosk", f"Failed for {text}"
        assert res["parameters"]["target_id"] == expected_app
        assert expected_app in DEFAULT_VALID_TARGETS
        assert res["latency_ms"] < 50.0


def test_canonical_search_and_system():
    """Verify search and system control intents."""
    # Search
    s_res = parse_intent("buscar blade runner")
    assert s_res["action"] == "search"
    assert s_res["parameters"]["search_query"] == "blade runner"

    s_res2 = parse_intent("busca videos de viajes espaciales")
    assert s_res2["action"] == "search"
    assert s_res2["parameters"]["search_query"] == "videos de viajes espaciales"

    # System control
    sys_res = parse_intent("mostrar panel")
    assert sys_res["action"] == "system_control"
    assert sys_res["parameters"]["command"] == "toggle_osd"

    sys_res2 = parse_intent("abrir ajustes")
    assert sys_res2["action"] == "system_control"
    assert sys_res2["parameters"]["command"] == "open_settings"

    sys_res3 = parse_intent("cerrar aplicacion")
    assert sys_res3["action"] == "system_control"
    assert sys_res3["parameters"]["command"] == "close_kiosk"


def test_whisper_phonetic_misspellings_and_aliases():
    """Verify robust recognition of real whisper.cpp output variants from TV speech."""
    # "posar" / "boussar" -> pause
    res_pause1 = parse_intent("posar")
    assert res_pause1["action"] == "media_control"
    assert res_pause1["parameters"]["key"] == "KEY_PLAYPAUSE"

    res_pause2 = parse_intent("boussar")
    assert res_pause2["action"] == "media_control"
    assert res_pause2["parameters"]["key"] == "KEY_PLAYPAUSE"

    # Phonetic entity correction for blade runner
    res_br = parse_intent("buscar blader anero")
    assert res_br["action"] == "search"
    assert res_br["parameters"]["search_query"] == "blade runner"

    # Spanish phonetic app names
    res_yt = parse_intent("abrir yutup")
    assert res_yt["action"] == "launch_kiosk"
    assert res_yt["parameters"]["target_id"] == "youtube"

    res_sp = parse_intent("abrir spotifi")
    assert res_sp["action"] == "launch_kiosk"
    assert res_sp["parameters"]["target_id"] == "spotify"


def test_compound_app_search_queries():
    """Verify compound queries extracting target app and nested query."""
    res = parse_intent("abrir youtube y buscar lofi chill")
    assert res["action"] == "launch_kiosk"
    assert res["parameters"]["target_id"] == "youtube"
    assert "lofi chill" in res["parameters"].get("search_query", "")


def test_security_sanitization_and_injection_rejection():
    """Verify absolute rejection of command injection, metacharacters, and path traversal."""
    malicious_inputs = [
        "abrir netflix; rm -rf /",
        "buscar blade runner && reboot",
        "pausar | cat /etc/shadow",
        "abrir youtube `id`",
        "subir volumen $(whoami)",
        "abrir ../../../etc/passwd",
        "abrir netflix > /dev/null",
        "pausar < /tmp/input",
        "test \x00 null byte",
    ]
    for bad_input in malicious_inputs:
        res = parse_intent(bad_input)
        assert res["action"] == "error", f"Should reject malicious input: {bad_input}"
        assert res["reason"] == "unsafe_input"

    # Empty inputs
    assert parse_intent("")["action"] == "error"
    assert parse_intent("   ")["action"] == "error"


def test_strict_allowlist_filtering():
    """Verify target_id is strictly constrained to caller's allowlist."""
    # When caller restricts allowlist to only netflix and spotify
    res = parse_intent("abrir youtube", valid_targets=["netflix", "spotify"])
    # youtube is not in allowlist -> falls back to search or unknown, not unapproved launch
    assert res.get("action") != "launch_kiosk" or res.get("parameters", {}).get("target_id") in ["netflix", "spotify"]


def test_intent_parsing_latency_bound():
    """Verify NLU intent parsing completes within <50ms (typically <1ms) on CPU."""
    sample_queries = [
        "abrir netflix",
        "pausar",
        "subir volumen",
        "buscar blade runner",
        "abrir youtube y buscar documentales de naturaleza",
        "silenciar el televisor",
        "mostrar panel de estado",
    ]
    latencies = []
    for q in sample_queries * 20: # 140 iterations
        t0 = time.perf_counter()
        res = parse_intent(q)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt_ms)
        assert res["action"] in ("launch_kiosk", "media_control", "search", "system_control")
        assert dt_ms < 50.0

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    assert avg_latency < 5.0, f"Average latency too high: {avg_latency:.2f}ms"
    assert max_latency < 50.0, f"Max latency exceeded budget: {max_latency:.2f}ms"


@pytest.mark.asyncio
async def test_offline_voice_pipeline_integration(monkeypatch):
    """Verify ai_pipeline.voice_command operates fully offline with local STT + NLU."""
    monkeypatch.setenv("LRP_STT_MOCK_RUNNER", "1")
    monkeypatch.setenv("LRP_STT_MOCK_TEXT", "abrir netflix")
    monkeypatch.setenv("LRP_MOCK_STT_TRANSCODE", "passthrough")

    from local_stt import generate_synthetic_pcm_wav
    dummy_audio = generate_synthetic_pcm_wav(duration_s=1.0, amplitude=12000, prefix_silence_s=0.1)

    result = await ai_pipeline.voice_command(dummy_audio, valid_targets=["netflix", "youtube"])
    assert result["ok"] is True
    assert result["text"] == "abrir netflix"
    assert result["intent"]["action"] == "launch_kiosk"
    assert result["intent"]["parameters"]["target_id"] == "netflix"
    assert "stt_metrics" in result
    assert result["nlu_latency_ms"] < 50.0

    # Empty audio rejection
    empty_res = await ai_pipeline.voice_command(b"")
    assert empty_res["ok"] is False
    assert empty_res["reason"] == "empty_audio"
