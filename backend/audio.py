"""Audio volume and mute control utilities using pactl/amixer."""
import subprocess
import shutil
import logging
from kiosk import gui_env

logger = logging.getLogger("audio")

def _run_cmd(cmd_list):
    try:
        subprocess.run(cmd_list, env=gui_env(), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error(f"Audio command failed {cmd_list}: {e}")

def get_audio_backend():
    if shutil.which("wpctl"):
        return "pipewire"
    elif shutil.which("pactl"):
        return "pulseaudio"
    elif shutil.which("amixer"):
        return "alsa"
    return None

def set_volume(delta_percent: int):
    backend = get_audio_backend()
    if backend == "pipewire":
        sign = "+" if delta_percent >= 0 else "-"
        _run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{abs(delta_percent)}%{sign}"])
    elif backend == "pulseaudio":
        sign = "+" if delta_percent >= 0 else "-"
        _run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{sign}{abs(delta_percent)}%"])
    elif backend == "alsa":
        sign = "+" if delta_percent >= 0 else "-"
        _run_cmd(["amixer", "-q", "sset", "Master", f"{abs(delta_percent)}%{sign}"])
    else:
        logger.warning("No audio backend found for volume control.")
        return False
    return True

def toggle_mute():
    backend = get_audio_backend()
    if backend == "pipewire":
        _run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
    elif backend == "pulseaudio":
        _run_cmd(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
    elif backend == "alsa":
        _run_cmd(["amixer", "-q", "sset", "Master", "toggle"])
    else:
        logger.warning("No audio backend found for mute control.")
        return False
    return True
