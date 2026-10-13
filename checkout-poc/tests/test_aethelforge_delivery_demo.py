"""Unit tests for read-only external JWS and body-binding checks."""
import base64
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from api.aethelforge_delivery_demo import _response_hash_claims, _verify_jws


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def sign_receipt(private_key, payload, kid="aethelforge-test"):
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    header = {"alg": "EdDSA", "kid": kid, "typ": "JWT"}
    segments = [
        b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode()),
        b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()),
    ]
    signing_input = (segments[0] + "." + segments[1]).encode("ascii")
    jws = ".".join(segments + [b64url(private_key.sign(signing_input))])
    jwks = {"keys": [{
        "kty": "OKP", "crv": "Ed25519", "alg": "EdDSA", "use": "sig",
        "kid": kid, "x": b64url(public_raw),
    }]}
    return jws, jwks


class AethelforgeDeliveryDemoTests(unittest.TestCase):
    def test_valid_jws_verifies_under_matching_published_key(self):
        body = b'{"sample":"same exact response bytes"}'
        payload = {"response": {"body_sha256": hashlib.sha256(body).hexdigest()}}
        jws, jwks = sign_receipt(Ed25519PrivateKey.generate(), payload)
        result = _verify_jws(jws, jwks)
        self.assertEqual(result["verdict"], "VERIFIED")
        self.assertEqual(result["payload"], payload)

    def test_tampered_payload_invalidates_signature(self):
        payload = {"response": {"body_sha256": "a" * 64}}
        jws, jwks = sign_receipt(Ed25519PrivateKey.generate(), payload)
        header, encoded_payload, signature = jws.split(".")
        tampered_payload = b64url(json.dumps({"response": {"body_sha256": "b" * 64}}, separators=(",", ":"), sort_keys=True).encode())
        result = _verify_jws(".".join([header, tampered_payload, signature]), jwks)
        self.assertEqual(result["verdict"], "NOT_VERIFIED")

    def test_unknown_key_id_remains_unknown(self):
        jws, jwks = sign_receipt(Ed25519PrivateKey.generate(), {"ok": True}, kid="not-published")
        jwks["keys"][0]["kid"] = "different-key"
        result = _verify_jws(jws, jwks)
        self.assertEqual(result["verdict"], "UNKNOWN")

    def test_hash_claims_are_found_inside_signed_payload(self):
        digest = "c" * 64
        claims = _response_hash_claims({"receipt": {"response": {"body_sha256": digest}}})
        self.assertEqual(claims, [{"path": "$.receipt.response.body_sha256", "value": digest}])


if __name__ == "__main__":
    unittest.main()
