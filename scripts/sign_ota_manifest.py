#!/usr/bin/env python3
"""
sign_ota_manifest.py — CLI to sign and verify LRP OTA manifests with Ed25519.
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

# Add backend to path for ota_security import
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from ota_security import (
    canonical_manifest_payload,
    verify_manifest_signature,
    get_ota_public_key_pem,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_keypair(out_priv: str, out_pub: str):
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()

    priv_pem = priv_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    Path(out_priv).write_bytes(priv_pem)
    Path(out_pub).write_bytes(pub_pem)
    print(f"Generated Ed25519 keypair:\n  Private key: {out_priv}\n  Public key:  {out_pub}")


def sign_manifest(manifest_path: str, key_path: str, pubkey_path: str | None = None):
    p = Path(manifest_path)
    if not p.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    k = Path(key_path)
    if not k.is_file():
        raise FileNotFoundError(f"Private key not found: {key_path}")

    priv_bytes = k.read_bytes()
    priv_key = serialization.load_pem_private_key(priv_bytes, password=None)
    if not isinstance(priv_key, ed25519.Ed25519PrivateKey):
        raise ValueError("Key is not an Ed25519 private key")

    with open(p, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    payload = canonical_manifest_payload(manifest)
    signature_bytes = priv_key.sign(payload)
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    manifest["signature"] = signature_b64

    # Determine public key for self-verification
    pub_pem = None
    if pubkey_path and Path(pubkey_path).is_file():
        pub_pem = Path(pubkey_path).read_text(encoding="utf-8")
    else:
        pub_key = priv_key.public_key()
        pub_pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    if not verify_manifest_signature(manifest, pub_pem):
        raise RuntimeError("Signature verification failed immediately after signing!")

    # Write back manifest formatted
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"[OK] Successfully signed manifest: {manifest_path}")
    print(f"  Canonical Payload: {payload.decode('utf-8', errors='replace')}")
    print(f"  Signature (b64):   {signature_b64}")


def verify_manifest(manifest_path: str, pubkey_path: str | None = None):
    p = Path(manifest_path)
    if not p.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(p, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    pub_pem = None
    if pubkey_path and Path(pubkey_path).is_file():
        pub_pem = Path(pubkey_path).read_text(encoding="utf-8")
    else:
        pub_pem = get_ota_public_key_pem()

    if verify_manifest_signature(manifest, pub_pem):
        print(f"[OK] Manifest signature is VALID: {manifest_path}")
        return 0
    else:
        print(f"[FAIL] Manifest signature is INVALID or missing: {manifest_path}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="Sign or verify LRP OTA manifests with Ed25519")
    parser.add_argument("--generate-key", nargs=2, metavar=("OUT_PRIV", "OUT_PUB"), help="Generate new Ed25519 keypair")
    parser.add_argument("--manifest", type=str, help="Path to manifest JSON file")
    parser.add_argument("--key", type=str, help="Path to private key PEM for signing")
    parser.add_argument("--pubkey", type=str, help="Path to public key PEM for verification")
    parser.add_argument("--verify-only", action="store_true", help="Verify signature on manifest without signing")

    args = parser.parse_args()

    if args.generate_key:
        generate_keypair(args.generate_key[0], args.generate_key[1])
        return 0

    if args.verify_only:
        if not args.manifest:
            parser.error("--manifest is required for --verify-only")
        return verify_manifest(args.manifest, args.pubkey)

    if args.manifest and args.key:
        sign_manifest(args.manifest, args.key, args.pubkey)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
