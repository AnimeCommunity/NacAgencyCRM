from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class SMTPSecretError(Exception):
    pass


def _fernet():
    key = getattr(settings, "CRM_SMTP_ENCRYPTION_KEY", "")
    if not key:
        raise ImproperlyConfigured(
            "CRM_SMTP_ENCRYPTION_KEY debe configurarse para guardar credenciales SMTP."
        )
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ImproperlyConfigured(
            "CRM_SMTP_ENCRYPTION_KEY no es una clave Fernet válida."
        ) from exc


def encrypt_smtp_password(password):
    return _fernet().encrypt(password.encode("utf-8")).decode("ascii")


def decrypt_smtp_password(ciphertext):
    if not ciphertext:
        return ""
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError) as exc:
        raise SMTPSecretError(
            "La credencial SMTP almacenada no puede descifrarse con la clave actual."
        ) from exc
