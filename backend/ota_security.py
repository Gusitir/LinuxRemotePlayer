"""
ota_security.py — Cryptographic signing verification and anti-downgrade validation for LRP OTA.
"""
import base64
import os
import re
from typing import Tuple, Optional
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

DEFAULT_OTA_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEANS6cE+yWj7iOFbEO+B3DsLY40Kla8nCLgoPnh+FSywI=
-----END PUBLIC KEY-----
"""


def get_ota_public_key_pem() -> str:
    """Retrieve public key PEM from configured path or default constant."""
    custom_path = os.getenv("LRP_OTA_PUBKEY_PATH")
    if custom_path and os.path.isfile(custom_path):
        try:
            return Path(custom_path).read_text(encoding="utf-8")
        except Exception:
            pass

    installed_path = "/opt/linuxremoteplayer/scripts/debian/lrp-ota-pub.pem"
    if os.path.isfile(installed_path):
        try:
            return Path(installed_path).read_text(encoding="utf-8")
        except Exception:
            pass

    repo_path = Path(__file__).resolve().parents[1] / "scripts" / "debian" / "lrp-ota-pub.pem"
    if repo_path.is_file():
        try:
            return repo_path.read_text(encoding="utf-8")
        except Exception:
            pass

    return DEFAULT_OTA_PUBLIC_KEY_PEM


def parse_version_tuple(v: str) -> Tuple[int, ...]:
    """Parse version string like '1.99.2' or 'v2.0.0' into tuple of integers."""
    clean = str(v).strip().lstrip("v")
    parts = []
    for chunk in clean.split("."):
        m = re.match(r"^(\d+)", chunk)
        if m:
            parts.append(int(m.group(1)))
        else:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def is_version_newer(remote_version: str, local_version: str) -> bool:
    """Anti-downgrade check: strictly demands remote_version > local_version."""
    try:
        remote_t = parse_version_tuple(remote_version)
        local_t = parse_version_tuple(local_version)
        return remote_t > local_t
    except Exception:
        return False


def canonical_manifest_payload(manifest: dict) -> bytes:
    """
    Construct canonical manifest payload for Ed25519 signing and verification:
    f"{version}|{architecture}|{filename}|{sha256}|{url}".encode("utf-8")
    """
    version = str(manifest.get("version", "")).strip()
    architecture = str(manifest.get("architecture", "")).strip()
    url = str(manifest.get("deb_url") or manifest.get("url", "")).strip()
    filename = str(manifest.get("filename") or (os.path.basename(url) if url else "")).strip()
    sha256_hash = str(manifest.get("sha256", "")).strip()

    payload_str = f"{version}|{architecture}|{filename}|{sha256_hash}|{url}"
    return payload_str.encode("utf-8")


def verify_manifest_signature(manifest: dict, public_key_pem: Optional[str] = None) -> bool:
    """
    Verify Ed25519 signature of an OTA manifest dictionary.
    Supports signature encoded in base64 or hex. Fail-closed on missing fields or invalid signature.
    """
    if not isinstance(manifest, dict):
        return False

    raw_sig = manifest.get("signature")
    if not raw_sig or not isinstance(raw_sig, str):
        return False

    raw_sig = raw_sig.strip()
    if not raw_sig:
        return False

    # Decode signature (try base64 first, then hex)
    sig_bytes = None
    try:
        sig_bytes = base64.b64decode(raw_sig)
        if len(sig_bytes) != 64:
            sig_bytes = None
    except Exception:
        sig_bytes = None

    if sig_bytes is None:
        try:
            sig_bytes = bytes.fromhex(raw_sig)
            if len(sig_bytes) != 64:
                sig_bytes = None
        except Exception:
            sig_bytes = None

    if not sig_bytes or len(sig_bytes) != 64:
        return False

    # Ensure required fields are not empty
    version = manifest.get("version")
    architecture = manifest.get("architecture")
    url = manifest.get("deb_url") or manifest.get("url")
    sha256_hash = manifest.get("sha256")
    if not (version and architecture and url and sha256_hash):
        return False

    payload = canonical_manifest_payload(manifest)

    pem = public_key_pem or get_ota_public_key_pem()
    try:
        pub_key = serialization.load_pem_public_key(pem.encode("utf-8"))
        if not isinstance(pub_key, ed25519.Ed25519PublicKey):
            return False
        pub_key.verify(sig_bytes, payload)
        return True
    except (InvalidSignature, Exception):
        return False


def validate_ota_manifest(manifest: dict, local_version: str, public_key_pem: Optional[str] = None) -> Tuple[bool, str]:
    """Validate OTA manifest against downgrade attack and cryptographic forgery."""
    if not isinstance(manifest, dict):
        return False, "manifest is not a valid dictionary"

    remote_version = str(manifest.get("version", "")).strip()
    if not remote_version:
        return False, "missing version in manifest"

    if not is_version_newer(remote_version, local_version):
        return False, f"anti-downgrade check failed: remote {remote_version} is not newer than local {local_version}"

    if not verify_manifest_signature(manifest, public_key_pem):
        return False, "invalid or missing cryptographic Ed25519 signature"

    return True, "valid"
