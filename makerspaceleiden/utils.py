import base64
import binascii
import hashlib
import json
import logging
import re
import sys

import cryptography
from django.http import HttpResponse
from dynamic_filenames import FilePattern
from jsonschema import validate

logger = logging.getLogger(__name__)

upload_to_pattern = FilePattern(
    filename_pattern="{app_label:.25}/{model_name:.30}/{uuid:base32}{ext}"
)


def validate_kv(payload):
    schema = {
        "title": "Simple flat KV of strings; 2-30 entries; simple names.",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "minProperties": 2,
        "maxProperties": 30,
        "additionalProperties": {"type": "string"},
        "propertyNames": {
            "pattern": "^[A-Za-z_][A-Za-z0-9_]*$",
        },
    }

    try:
        if not isinstance(payload, str):
            raise Exception("JSON not a string")

        if len(payload) < 5 or len(payload) > 1000:
            raise Exception("JSON too short or too long")

        decoded = json.loads(payload)
        validate(instance=decoded, schema=schema)

        return decoded
    except Exception as e:
        ex_type, ex_value, ex_traceback = sys.exc_info()
        erm = str(ex_value).split("\n", 1)[0]
        logger.error(f"Could not parse Plain KV JSON: {type(e).__name__} {erm}")
        pass
    return {}


def pemToSHA256Fingerprint(pem, justkey=False):
    try:
        pem = pem[27:-25]
        der = base64.b64decode(pem.encode("ascii"))
        if justkey:
            cert = cryptography.x509.load_pem_x509_certificate(pem)
            public_key = cert.public_key()
            der = public_key.public_bytes()
        return hashlib.sha256(der).hexdigest()
    except Exception:
        pass
    logger.error("Could not parse pem for finrprint: {}".format(pem))
    return None


def hexsha2pin(sha256_hex_a, sha256_hex_b):
    a = binascii.unhexlify(sha256_hex_a)
    b = binascii.unhexlify(sha256_hex_b)
    if (len(a) != 32) or (len(b) != 32):
        raise NameError("Not a SHA256")
    fp = hashlib.sha256(a + b).hexdigest()
    return fp[:6].upper()


def client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def client_cert(request, justkey=False):
    return cert_sha("SSL_CLIENT_CERT", request, justkey=justkey)


def server_cert(request, justkey=False):
    return cert_sha("SSL_SERVER_CERT", request, justkey=justkey)


def cert_sha(src, request, justkey=False):
    if "runserver" in sys.argv:
        src = "HTTP_" + src
        logger.warn(
            "Warning: sourcing SSL information for {} from INSECURE header !!".format(
                src
            )
        )

    cert = request.META.get(src, None)

    if cert is None:
        logger.error("Bad request, missing {}".format(src))
        return HttpResponse(
            "No client identifier, rejecting", status=400, content_type="text/plain"
        )

    sha = pemToSHA256Fingerprint(cert, justkey=justkey)
    if sha is None:
        logger.error("Bad request, cannot derive sha from {}".format(src))
        return HttpResponse(
            "No client sha, rejecting", status=400, content_type="text/plain"
        )
    return sha


pattern = re.compile("^(a|e)l( |-)|van der|van|de|ten", re.IGNORECASE)


def derive_initials(first_name, last_name):
    normalized_last_name = re.sub(pattern, "", last_name).strip()
    return (first_name[:1] + normalized_last_name[:1]).upper()
