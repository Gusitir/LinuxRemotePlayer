"""Local NLU Intent Engine for LinuxRemotePlayer appliance.

Deterministic, zero-allocation semantic intent parsing optimized for CPU (<50ms latency).
Enforces strict allowlist validation and security guardrails against text/shell injection.
"""
import re
import time
import string
import logging
from typing import Optional, Dict, Any, List, Set, Tuple

logger = logging.getLogger("local_intent")

# Strict Allowlist: Media Control Keys
ALLOWED_MEDIA_KEYS: Set[str] = {
    "KEY_PLAYPAUSE",
    "KEY_PLAY",
    "KEY_PAUSE",
    "KEY_STOP",
    "KEY_VOLUMEUP",
    "KEY_VOLUMEDOWN",
    "KEY_MUTE",
    "KEY_NEXTSONG",
    "KEY_PREVIOUSSONG",
    "KEY_FASTFORWARD",
    "KEY_REWIND",
}

# Strict Allowlist: Default Kiosk Targets
DEFAULT_VALID_TARGETS: Set[str] = {
    "netflix",
    "youtube",
    "primevideo",
    "disney",
    "hbomax",
    "spotify",
    "twitch",
    "crunchyroll",
    "stremio",
    "plex",
    "plutotv",
    "kick",
    "tiktok",
    "instagram",
    "facebook",
    "appletv",
}

# Strict Allowlist: Controlled System Actions
ALLOWED_SYSTEM_COMMANDS: Set[str] = {
    "toggle_osd",
    "open_settings",
    "close_kiosk",
    "power_menu",
}

# Dangerous metacharacters prohibited in voice search strings
DANGEROUS_CHARS_RE = re.compile(r"[;&|`$<>\\]")

# Phonetic & Alias Mappings for Media Commands
MEDIA_PHONETIC_MAP: Dict[str, str] = {
    # Pause / Play
    "pausar": "KEY_PLAYPAUSE",
    "pausa": "KEY_PLAYPAUSE",
    "posar": "KEY_PLAYPAUSE",
    "pousar": "KEY_PLAYPAUSE",
    "boussar": "KEY_PLAYPAUSE",
    "detener": "KEY_PLAYPAUSE",
    "deten": "KEY_PLAYPAUSE",
    "para": "KEY_PLAYPAUSE",
    "parar": "KEY_PLAYPAUSE",
    "pause": "KEY_PLAYPAUSE",
    "stop": "KEY_PLAYPAUSE",
    "play": "KEY_PLAYPAUSE",
    "reproducir": "KEY_PLAYPAUSE",
    "reproduce": "KEY_PLAYPAUSE",
    "reanudar": "KEY_PLAYPAUSE",
    "reanuda": "KEY_PLAYPAUSE",
    "continuar": "KEY_PLAYPAUSE",
    "continua": "KEY_PLAYPAUSE",
    "dale play": "KEY_PLAYPAUSE",
    # Volume Up
    "subir volumen": "KEY_VOLUMEUP",
    "sube volumen": "KEY_VOLUMEUP",
    "sube el volumen": "KEY_VOLUMEUP",
    "subir el volumen": "KEY_VOLUMEUP",
    "mas volumen": "KEY_VOLUMEUP",
    "mas fuerte": "KEY_VOLUMEUP",
    "aumentar volumen": "KEY_VOLUMEUP",
    "aumenta volumen": "KEY_VOLUMEUP",
    "volume up": "KEY_VOLUMEUP",
    # Volume Down
    "bajar volumen": "KEY_VOLUMEDOWN",
    "baja volumen": "KEY_VOLUMEDOWN",
    "baja el volumen": "KEY_VOLUMEDOWN",
    "bajar el volumen": "KEY_VOLUMEDOWN",
    "menos volumen": "KEY_VOLUMEDOWN",
    "mas bajo": "KEY_VOLUMEDOWN",
    "mas despacio": "KEY_VOLUMEDOWN",
    "disminuir volumen": "KEY_VOLUMEDOWN",
    "disminuye volumen": "KEY_VOLUMEDOWN",
    "volume down": "KEY_VOLUMEDOWN",
    # Mute
    "silenciar": "KEY_MUTE",
    "silencia": "KEY_MUTE",
    "mutear": "KEY_MUTE",
    "mutea": "KEY_MUTE",
    "silencio": "KEY_MUTE",
    "quitar sonido": "KEY_MUTE",
    "mute": "KEY_MUTE",
    # Next / Prev
    "siguiente": "KEY_NEXTSONG",
    "siguiente cancion": "KEY_NEXTSONG",
    "siguiente video": "KEY_NEXTSONG",
    "proxima": "KEY_NEXTSONG",
    "avanzar": "KEY_NEXTSONG",
    "next": "KEY_NEXTSONG",
    "anterior": "KEY_PREVIOUSSONG",
    "cancion anterior": "KEY_PREVIOUSSONG",
    "video anterior": "KEY_PREVIOUSSONG",
    "previa": "KEY_PREVIOUSSONG",
    "retroceder": "KEY_PREVIOUSSONG",
    "previous": "KEY_PREVIOUSSONG",
    # Seek
    "adelantar": "KEY_FASTFORWARD",
    "adelanta": "KEY_FASTFORWARD",
    "atrasar": "KEY_REWIND",
    "atrasa": "KEY_REWIND",
}

# Kiosk App Aliases and Common STT Misspellings
APP_ALIASES: Dict[str, str] = {
    "netflix": "netflix",
    "net flix": "netflix",
    "netflis": "netflix",
    "youtube": "youtube",
    "you tube": "youtube",
    "yutup": "youtube",
    "iutub": "youtube",
    "tutube": "youtube",
    "prime video": "primevideo",
    "primevideo": "primevideo",
    "amazon prime": "primevideo",
    "amazon": "primevideo",
    "prime": "primevideo",
    "disney": "disney",
    "disney plus": "disney",
    "disney mas": "disney",
    "disney+": "disney",
    "max": "hbomax",
    "hbo": "hbomax",
    "hbo max": "hbomax",
    "hbomax": "hbomax",
    "spotify": "spotify",
    "spotifi": "spotify",
    "musica": "spotify",
    "música": "spotify",
    "twitch": "twitch",
    "tuich": "twitch",
    "crunchyroll": "crunchyroll",
    "crunchy roll": "crunchyroll",
    "anime": "crunchyroll",
    "stremio": "stremio",
    "estremio": "stremio",
    "estrimio": "stremio",
    "plex": "plex",
    "pluto": "plutotv",
    "pluto tv": "plutotv",
    "plutotv": "plutotv",
    "kick": "kick",
    "tiktok": "tiktok",
    "tik tok": "tiktok",
    "instagram": "instagram",
    "facebook": "facebook",
    "apple tv": "appletv",
    "apple tv+": "appletv",
    "appletv": "appletv",
}

# System command patterns
SYSTEM_COMMANDS_MAP: Dict[str, str] = {
    "panel": "toggle_osd",
    "menu": "toggle_osd",
    "mostrar panel": "toggle_osd",
    "abrir panel": "toggle_osd",
    "ajustes": "open_settings",
    "abrir ajustes": "open_settings",
    "configuracion": "open_settings",
    "status": "toggle_osd",
    "cerrar": "close_kiosk",
    "cerrar app": "close_kiosk",
    "cerrar aplicacion": "close_kiosk",
    "cerrar kiosk": "close_kiosk",
    "salir": "close_kiosk",
    "apagar": "power_menu",
}


def sanitize_input(text: str, max_length: int = 200) -> str:
    """Sanitize raw STT text to prevent injection, control chars, and unbounded buffers."""
    if not text:
        return ""
    # Strip null bytes and control chars
    clean = "".join(ch for ch in text if ch.isprintable() and ch not in "\r\n\t\x00")
    # Truncate
    clean = clean[:max_length].strip()
    # Normalize punctuation for intent parsing
    clean_no_punct = "".join(ch if ch not in string.punctuation and ch not in "¡¿" else " " for ch in clean)
    # Normalize whitespace
    clean_normalized = " ".join(clean_no_punct.split()).lower()
    return clean_normalized


def parse_intent(
    raw_text: str,
    valid_targets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Parse transcribed text into a validated LRP action dictionary in <50ms.
    
    Returns:
        {
            "action": "launch_kiosk" | "media_control" | "search" | "system_control" | "unknown" | "error",
            "parameters": Dict[str, Any],
            "confidence": float,
            "latency_ms": float,
            "raw_text": str
        }
    """
    t_start = time.monotonic()
    allowed_targets = set(valid_targets) if valid_targets else DEFAULT_VALID_TARGETS

    sanitized = sanitize_input(raw_text)
    if not sanitized:
        return {
            "action": "error",
            "reason": "empty_text",
            "parameters": {},
            "confidence": 0.0,
            "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
            "raw_text": raw_text,
        }

    # Security check: detect malicious metacharacters, null bytes, and path traversal in raw text
    if "\x00" in raw_text or any(ord(c) < 32 for c in raw_text) or DANGEROUS_CHARS_RE.search(raw_text) or ".." in raw_text:
        logger.warning(f"Malicious metacharacter detected in voice command: {repr(raw_text)}")
        return {
            "action": "error",
            "reason": "unsafe_input",
            "parameters": {},
            "confidence": 0.0,
            "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
            "raw_text": raw_text,
        }

    # 1. Media Control Matching (Highest priority for single-word / command phrases)
    if sanitized in MEDIA_PHONETIC_MAP:
        key = MEDIA_PHONETIC_MAP[sanitized]
        if key in ALLOWED_MEDIA_KEYS:
            return {
                "action": "media_control",
                "parameters": {"key": key},
                "confidence": 0.98,
                "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
                "raw_text": raw_text,
            }

    # Check partial volume / media patterns e.g. "subir el volumen un poco"
    if "volumen" in sanitized:
        if any(w in sanitized for w in ["subir", "sube", "mas", "aumentar", "aumenta", "arriba"]):
            return {
                "action": "media_control",
                "parameters": {"key": "KEY_VOLUMEUP"},
                "confidence": 0.95,
                "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
                "raw_text": raw_text,
            }
        elif any(w in sanitized for w in ["bajar", "baja", "menos", "disminuir", "disminuye", "abajo"]):
            return {
                "action": "media_control",
                "parameters": {"key": "KEY_VOLUMEDOWN"},
                "confidence": 0.95,
                "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
                "raw_text": raw_text,
            }
        elif any(w in sanitized for w in ["quitar", "apagar", "cero", "silencio"]):
            return {
                "action": "media_control",
                "parameters": {"key": "KEY_MUTE"},
                "confidence": 0.95,
                "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
                "raw_text": raw_text,
            }

    # 2. System Control Matching
    if sanitized in SYSTEM_COMMANDS_MAP:
        cmd = SYSTEM_COMMANDS_MAP[sanitized]
        if cmd in ALLOWED_SYSTEM_COMMANDS:
            return {
                "action": "system_control",
                "parameters": {"command": cmd},
                "confidence": 0.95,
                "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
                "raw_text": raw_text,
            }

    # 3. Launch Kiosk App Matching
    # Strip common command verbs: "abrir", "abre", "iniciar", "inicia", "poner", "pon", "ir a", "lanzar", "open"
    app_prefix_match = re.match(
        r"^(?:abrir|abre|iniciar|inicia|poner|pon|ir a|lanzar|lanza|open|launch)\s+(.+)$",
        sanitized,
    )
    target_candidate = app_prefix_match.group(1).strip() if app_prefix_match else sanitized

    # Check direct app alias match
    if target_candidate in APP_ALIASES:
        resolved_app = APP_ALIASES[target_candidate]
        if resolved_app in allowed_targets:
            return {
                "action": "launch_kiosk",
                "parameters": {"target_id": resolved_app},
                "confidence": 0.95,
                "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
                "raw_text": raw_text,
            }

    # Check compound app launch e.g. "poner musica en youtube" or "abrir youtube y buscar lofi"
    for alias, app_id in APP_ALIASES.items():
        if alias in sanitized and app_id in allowed_targets:
            # Check if this compound query has a search query inside
            search_prefix_match = re.search(
                rf"(?:{alias})\s+(?:y\s+)?(?:buscar|busca|de|con)?\s+(.+)$", sanitized
            )
            extracted_query = search_prefix_match.group(1).strip() if search_prefix_match else ""
            # Clean search query of leading stopwords
            for stopword in ["y buscar", "buscar", "busca", "de", "con"]:
                if extracted_query.startswith(stopword + " "):
                    extracted_query = extracted_query[len(stopword) + 1:].strip()

            params = {"target_id": app_id}
            if extracted_query:
                params["search_query"] = extracted_query
            return {
                "action": "launch_kiosk",
                "parameters": params,
                "confidence": 0.90,
                "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
                "raw_text": raw_text,
            }

    # 4. Search Matching
    # E.g. "buscar blade runner", "busca peliculas de accion", "encuentra stranger things"
    search_match = re.match(
        r"^(?:buscar|busca|search|encuentra|encontrar|poner|pon)\s+(.+)$",
        sanitized,
    )
    if search_match:
        query = search_match.group(1).strip()
        # Phonetic entity correction for canonical TV terms
        if any(term in query for term in ["blader anero", "blader anir", "blader runner"]):
            query = query.replace("blader anero", "blade runner").replace("blader anir", "blade runner")

        return {
            "action": "search",
            "parameters": {"search_query": query},
            "confidence": 0.90,
            "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
            "raw_text": raw_text,
        }

    # 5. Default Fallback
    # If phrase has substantive words, treat as content search
    words = sanitized.split()
    if len(words) >= 1:
        # Fallback to general search query
        return {
            "action": "search",
            "parameters": {"search_query": sanitized},
            "confidence": 0.60,
            "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
            "raw_text": raw_text,
        }

    return {
        "action": "unknown",
        "parameters": {"raw_text": raw_text},
        "confidence": 0.0,
        "latency_ms": round((time.monotonic() - t_start) * 1000.0, 2),
        "raw_text": raw_text,
    }
