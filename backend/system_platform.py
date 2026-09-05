"""Decoupled system platform API and OS hardware abstractions (/api/system/*).
Provides PipeWire audio control, NetworkManager Wi-Fi scanning/connection,
bluetoothctl device inspection, and xrandr display management.
Safely falls back with mock/empty data on non-Linux or dev environments.
"""
import os
import re
import shutil
import logging
import subprocess
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Header, Query
from pydantic import BaseModel, Field, field_validator

try:
    from kiosk import gui_env
except ImportError:
    def gui_env():
        return os.environ.copy()

logger = logging.getLogger("system_platform")
router = APIRouter(prefix="/api/system", tags=["system"])


def is_authorized(request: Request, x_auth_token: str = Header(default=""), token: str = Query(default="")) -> bool:
    """Validate request is either local or paired with a valid token."""
    client_host = request.client.host if request.client else ""
    if client_host.startswith("::ffff:"):
        client_host = client_host.replace("::ffff:", "")
    if client_host in ["127.0.0.1", "localhost", "::1", "testclient"]:
        return True
    
    auth_tok = x_auth_token or token
    if auth_tok:
        try:
            from auth import verify_access
            if verify_access(auth_tok):
                return True
        except ImportError:
            pass
    raise HTTPException(status_code=401, detail="Unauthorized")


# --- Audio (PipeWire / WirePlumber) ---

def parse_wpctl_status(status_output: str) -> Dict[str, Any]:
    """Parse `wpctl status` text output to extract audio sinks, default sink, and volume."""
    sinks = []
    active_sink = None
    in_sinks_section = False

    for line in status_output.splitlines():
        if "Sinks:" in line:
            in_sinks_section = True
            continue
        if in_sinks_section:
            # End of sinks section if we hit next section or empty indentation
            if re.match(r"^\s*[├└]─\s+[A-Za-z]+", line) or (line.strip() and not line.startswith(" ") and not line.startswith("│")):
                break
            
            # Match sink line: e.g. " *   49. Built-in Audio Analog Stereo        [vol: 0.65]"
            # or "      50. GA106 High Definition Audio Controller Digital Stereo (HDMI) [vol: 1.00 MUTED]"
            m = re.search(r"(\*?)\s*(\d+)\.\s+([^\[]+?)(?:\s+\[vol:\s*([0-9.]+)(?:\s+(MUTED))?\])?$", line)
            if m:
                is_default = bool(m.group(1))
                sink_id = m.group(2)
                name = m.group(3).strip()
                vol_str = m.group(4)
                muted = bool(m.group(5))
                
                vol = int(float(vol_str) * 100) if vol_str else 100
                if is_default:
                    active_sink = sink_id
                
                sinks.append({
                    "id": sink_id,
                    "name": name,
                    "active": is_default,
                    "volume": vol,
                    "muted": muted
                })

    if not active_sink and sinks:
        active_sink = sinks[0]["id"]
        sinks[0]["active"] = True

    active_vol = 100
    active_muted = False
    for s in sinks:
        if s["id"] == active_sink:
            active_vol = s["volume"]
            active_muted = s["muted"]
            break

    return {
        "backend": "pipewire",
        "active_sink": active_sink,
        "volume": active_vol,
        "muted": active_muted,
        "sinks": sinks
    }


def get_audio_info() -> Dict[str, Any]:
    """Inspect PipeWire audio state via wpctl or return graceful dev fallback."""
    wpctl_bin = shutil.which("wpctl")
    if not wpctl_bin:
        return {
            "backend": "none",
            "active_sink": "dummy",
            "volume": 100,
            "muted": False,
            "sinks": [
                {"id": "dummy", "name": "Simulated Audio Output", "active": True, "volume": 100, "muted": False}
            ]
        }
    
    try:
        proc = subprocess.run(
            [wpctl_bin, "status"],
            capture_output=True, text=True, timeout=5, check=False
        )
        if proc.returncode == 0 and proc.stdout:
            info = parse_wpctl_status(proc.stdout)
            # Try getting accurate volume for default sink
            vol_proc = subprocess.run(
                [wpctl_bin, "get-volume", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True, text=True, timeout=3, check=False
            )
            if vol_proc.returncode == 0:
                vm = re.search(r"Volume:\s*([0-9.]+)(?:\s+\[(MUTED)\])?", vol_proc.stdout)
                if vm:
                    info["volume"] = int(float(vm.group(1)) * 100)
                    info["muted"] = bool(vm.group(2))
            return info
    except Exception as e:
        logger.warning(f"Error querying wpctl audio info: {e}")

    return {
        "backend": "pipewire",
        "active_sink": None,
        "volume": 100,
        "muted": False,
        "sinks": []
    }


class SetSinkBody(BaseModel):
    sink_id: str = Field(..., min_length=1, max_length=64)

    @field_validator("sink_id")
    @classmethod
    def validate_sink_id(cls, v: str):
        v = v.strip()
        if not re.match(r"^[0-9@a-zA-Z_.-]+$", v):
            raise ValueError("Invalid sink_id format")
        return v


class SetVolumeBody(BaseModel):
    volume: int = Field(..., ge=0, le=150)
    sink_id: str = Field(default="@DEFAULT_AUDIO_SINK@", max_length=64)

    @field_validator("sink_id")
    @classmethod
    def validate_sink_id(cls, v: str):
        v = v.strip()
        if not re.match(r"^[0-9@a-zA-Z_.-]+$", v):
            raise ValueError("Invalid sink_id format")
        return v


@router.get("/audio", dependencies=[Depends(is_authorized)])
def get_audio():
    return get_audio_info()


@router.post("/audio/sink", dependencies=[Depends(is_authorized)])
def set_audio_sink(body: SetSinkBody):
    wpctl_bin = shutil.which("wpctl")
    if not wpctl_bin:
        return {"ok": True, "active_sink": body.sink_id, "mock": True}
    try:
        res = subprocess.run(
            [wpctl_bin, "set-default", body.sink_id],
            capture_output=True, text=True, timeout=5, check=False
        )
        if res.returncode == 0:
            return {"ok": True, "active_sink": body.sink_id}
        raise HTTPException(status_code=400, detail=res.stderr.strip() or "Failed to set default sink")
    except Exception as e:
        logger.error(f"Error setting audio sink: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/volume", dependencies=[Depends(is_authorized)])
def set_audio_volume(body: SetVolumeBody):
    wpctl_bin = shutil.which("wpctl")
    if not wpctl_bin:
        return {"ok": True, "volume": body.volume, "mock": True}
    try:
        vol_arg = f"{body.volume}%"
        res = subprocess.run(
            [wpctl_bin, "set-volume", body.sink_id, vol_arg],
            capture_output=True, text=True, timeout=5, check=False
        )
        if res.returncode == 0:
            return {"ok": True, "volume": body.volume, "sink": body.sink_id}
        raise HTTPException(status_code=400, detail=res.stderr.strip() or "Failed to set volume")
    except Exception as e:
        logger.error(f"Error setting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Wi-Fi (NetworkManager nmcli) ---

def parse_nmcli_wifi_list(output: str) -> Dict[str, Any]:
    """Parse `nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE device wifi list`."""
    networks_map: Dict[str, Dict[str, Any]] = {}
    connected_ssid = None

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: SSID:SIGNAL:SECURITY:IN-USE
        parts = line.split(":")
        if len(parts) >= 4:
            in_use = parts[-1].strip() in ("*", "yes")
            sec = parts[-2].strip() or "OPEN"
            sig_str = parts[-3].strip()
            ssid = ":".join(parts[:-3]).strip()
            
            if not ssid or ssid == "--":
                continue

            try:
                sig = int(sig_str)
            except ValueError:
                sig = 0

            if in_use:
                connected_ssid = ssid

            if ssid not in networks_map or sig > networks_map[ssid]["signal"]:
                networks_map[ssid] = {
                    "ssid": ssid,
                    "signal": sig,
                    "security": sec,
                    "connected": in_use
                }

    networks = sorted(networks_map.values(), key=lambda x: x["signal"], reverse=True)
    return {
        "available": True,
        "connected": connected_ssid,
        "networks": networks
    }


def get_wifi_info() -> Dict[str, Any]:
    """Inspect Wi-Fi networks via nmcli or return graceful fallback."""
    nmcli_bin = shutil.which("nmcli")
    if not nmcli_bin:
        return {
            "available": False,
            "connected": None,
            "networks": []
        }
    try:
        proc = subprocess.run(
            [nmcli_bin, "-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "device", "wifi", "list"],
            capture_output=True, text=True, timeout=10, check=False
        )
        if proc.returncode == 0:
            return parse_nmcli_wifi_list(proc.stdout)
    except Exception as e:
        logger.warning(f"Error scanning Wi-Fi via nmcli: {e}")

    return {
        "available": True,
        "connected": None,
        "networks": []
    }


class WifiConnectBody(BaseModel):
    ssid: str = Field(..., min_length=1, max_length=64)
    password: Optional[str] = Field(default=None, max_length=128)

    @field_validator("ssid")
    @classmethod
    def validate_ssid(cls, v: str):
        v = v.strip()
        if not v or any(ord(c) < 32 for c in v):
            raise ValueError("Invalid characters in SSID")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]):
        if v is not None:
            if any(ord(c) < 32 for c in v):
                raise ValueError("Invalid characters in password")
        return v


@router.get("/wifi", dependencies=[Depends(is_authorized)])
def get_wifi():
    return get_wifi_info()


@router.post("/wifi/connect", dependencies=[Depends(is_authorized)])
def connect_wifi(body: WifiConnectBody):
    nmcli_bin = shutil.which("nmcli")
    if not nmcli_bin:
        return {"ok": False, "error": "nmcli not available on this platform"}

    cmd = [nmcli_bin, "device", "wifi", "connect", body.ssid]
    if body.password:
        cmd.extend(["password", body.password])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25, check=False)
        if proc.returncode == 0:
            return {"ok": True, "message": f"Connected to {body.ssid}"}
        error_msg = proc.stderr.strip() or proc.stdout.strip() or "Connection failed"
        return {"ok": False, "error": error_msg}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Connection timed out"}
    except Exception as e:
        logger.error(f"Error connecting to Wi-Fi SSID '{body.ssid}': {e}")
        return {"ok": False, "error": str(e)}


# --- Bluetooth (bluetoothctl) ---

def parse_bluetoothctl_devices(devices_out: str, paired_out: str = "") -> List[Dict[str, Any]]:
    """Parse bluetoothctl devices output."""
    paired_macs = set()
    for line in paired_out.splitlines():
        m = re.search(r"Device\s+([0-9A-Fa-f:]{17})", line)
        if m:
            paired_macs.add(m.group(1).upper())

    devices = []
    for line in devices_out.splitlines():
        m = re.search(r"Device\s+([0-9A-Fa-f:]{17})\s+(.*)$", line)
        if m:
            mac = m.group(1).upper()
            name = m.group(2).strip()
            devices.append({
                "mac": mac,
                "name": name,
                "paired": mac in paired_macs
            })
    return devices


def get_bluetooth_info() -> Dict[str, Any]:
    """Inspect Bluetooth adapter and devices via bluetoothctl."""
    bt_bin = shutil.which("bluetoothctl")
    if not bt_bin:
        return {
            "available": False,
            "powered": False,
            "devices": []
        }
    try:
        show_proc = subprocess.run(
            [bt_bin, "show"],
            capture_output=True, text=True, timeout=5, check=False
        )
        powered = "Powered: yes" in (show_proc.stdout or "")

        dev_proc = subprocess.run(
            [bt_bin, "devices"],
            capture_output=True, text=True, timeout=5, check=False
        )
        paired_proc = subprocess.run(
            [bt_bin, "devices", "Paired"],
            capture_output=True, text=True, timeout=5, check=False
        )
        devices = parse_bluetoothctl_devices(dev_proc.stdout or "", paired_proc.stdout or "")

        return {
            "available": True,
            "powered": powered,
            "devices": devices
        }
    except Exception as e:
        logger.warning(f"Error querying bluetoothctl: {e}")

    return {
        "available": True,
        "powered": False,
        "devices": []
    }


@router.get("/bluetooth", dependencies=[Depends(is_authorized)])
def get_bluetooth():
    return get_bluetooth_info()


# --- Display (xrandr) ---

def parse_xrandr_output(output: str) -> List[Dict[str, Any]]:
    """Parse xrandr --current output to extract connected monitors, current resolution, and refresh rate."""
    displays = []
    current_display = None

    for line in output.splitlines():
        # Match output line: "HDMI-1 connected primary 1920x1080+0+0 ..." or "DP-1 disconnected ..."
        out_match = re.match(r"^([A-Za-z0-9-]+)\s+(connected|disconnected)(?:\s+(primary))?", line)
        if out_match:
            port = out_match.group(1)
            connected = out_match.group(2) == "connected"
            primary = bool(out_match.group(3))
            
            current_display = {
                "output": port,
                "connected": connected,
                "primary": primary,
                "current_mode": None,
                "refresh_rate": None,
                "modes": []
            }
            displays.append(current_display)
            continue

        if current_display and current_display["connected"]:
            # Mode lines: e.g. "   1920x1080     60.00*+  50.00    59.94"
            mode_match = re.match(r"^\s+([0-9]+x[0-9]+)\s+(.*)$", line)
            if mode_match:
                res = mode_match.group(1)
                rates_part = mode_match.group(2)
                if res not in current_display["modes"]:
                    current_display["modes"].append(res)
                
                # Active rate marked by '*'
                rate_match = re.search(r"([0-9.]+)\*", rates_part)
                if rate_match:
                    current_display["current_mode"] = res
                    current_display["refresh_rate"] = rate_match.group(1)

    return displays


def get_display_info() -> Dict[str, Any]:
    """Query current display state via xrandr or return graceful fallback."""
    xrandr_bin = shutil.which("xrandr")
    if not xrandr_bin:
        return {
            "available": False,
            "displays": []
        }
    try:
        proc = subprocess.run(
            [xrandr_bin, "--current"],
            env=gui_env(), capture_output=True, text=True, timeout=5, check=False
        )
        if proc.returncode == 0:
            displays = parse_xrandr_output(proc.stdout)
            return {
                "available": True,
                "displays": displays
            }
    except Exception as e:
        logger.warning(f"Error querying xrandr: {e}")

    return {
        "available": True,
        "displays": []
    }


@router.get("/display", dependencies=[Depends(is_authorized)])
def get_display():
    return get_display_info()
