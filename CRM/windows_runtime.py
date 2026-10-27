import argparse
import base64
import ctypes
import hashlib
import hmac
import json
import logging
import os
import secrets
import shutil
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import webbrowser
import zipfile
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


APP_NAME = "NacAgencyCRM"
DEFAULT_PORT = 8000
HEALTH_PATH = "/__nacagencycrm__/health"
STOP_PATH = "/__nacagencycrm__/stop"
INSTANCE_TOKEN_HEADER = "HTTP_X_NACAGENCYCRM_INSTANCE_TOKEN"
MAINTENANCE_MUTEX_NAMES = (
    "NacAgencyCRM-Installer-Maintenance-v1",
    r"Global\NacAgencyCRM-Installer-Maintenance-v1",
)
INSTALLER_CAPABILITY_TOKEN_ENV = "NACAGENCYCRM_INSTALLER_CAPABILITY_TOKEN"
INSTALLER_CAPABILITY_FILE_ENV = "NACAGENCYCRM_INSTALLER_CAPABILITY_FILE"
TRIAL_ADMIN_USERNAME = "aniokku"
TRIAL_ADMIN_PASSWORD_HASH = (
    "pbkdf2_sha256$1000000$v7NrUsxgkBVkGqnDxnG8I2$"
    "y7ydgxFlaI014fAOWNJoQfWu3vq+/gzYbEcXFgy0vk0="
)


class InterprocessFileLock:
    def __init__(self, path):
        self.path = Path(path)
        self.descriptor = None
        self.owned = False

    def acquire(self, timeout=0):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b"0")
            os.fsync(descriptor)

        deadline = time.monotonic() + timeout
        while True:
            try:
                os.lseek(descriptor, 0, os.SEEK_SET)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.descriptor = descriptor
                self.owned = True
                return True
            except OSError:
                if time.monotonic() >= deadline:
                    os.close(descriptor)
                    return False
                time.sleep(0.05)

    def close(self):
        if not self.owned or self.descriptor is None:
            return
        os.lseek(self.descriptor, 0, os.SEEK_SET)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self.descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.descriptor, fcntl.LOCK_UN)
        os.close(self.descriptor)
        self.descriptor = None
        self.owned = False


class _CallbackAfterClose:
    def __init__(self, body, callback):
        self.body = body
        self.callback = callback
        self.closed = False

    def __iter__(self):
        yield self.body

    def close(self):
        if not self.closed:
            self.closed = True
            self.callback()


class AuthenticatedLocalControl:
    def __init__(self, application, instance_token, stop_callback):
        self.application = application
        self.instance_token = instance_token
        self.stop_callback = stop_callback

    def _authorized(self, environ):
        supplied = environ.get(INSTANCE_TOKEN_HEADER, "")
        return bool(supplied) and hmac.compare_digest(supplied, self.instance_token)

    @staticmethod
    def _json_response(start_response, status, payload):
        body = json.dumps(payload).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [body]

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO")
        if path not in {HEALTH_PATH, STOP_PATH}:
            return self.application(environ, start_response)
        expected_method = "GET" if path == HEALTH_PATH else "POST"
        if environ.get("REQUEST_METHOD") != expected_method:
            return self._json_response(start_response, "405 Method Not Allowed", {"error": "method_not_allowed"})
        if not self._authorized(environ):
            return self._json_response(start_response, "403 Forbidden", {"error": "forbidden"})
        if path == HEALTH_PATH:
            return self._json_response(
                start_response,
                "200 OK",
                {"application": APP_NAME, "status": "ok"},
            )

        body = json.dumps({"application": APP_NAME, "status": "stopping"}).encode("utf-8")
        start_response(
            "200 OK",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ],
        )
        return _CallbackAfterClose(body, self.stop_callback)


def _authenticated_control_request(port, path, instance_token, method="GET", timeout=1):
    request = Request(
        f"http://127.0.0.1:{port}{path}",
        headers={"X-NacAgencyCRM-Instance-Token": instance_token},
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def probe_running_instance(port, instance_token, timeout=1):
    payload = _authenticated_control_request(
        port, HEALTH_PATH, instance_token, timeout=timeout
    )
    return bool(
        payload
        and payload.get("application") == APP_NAME
        and payload.get("status") == "ok"
    )


def _read_runtime_state(path):
    if path is None or not Path(path).is_file():
        return {}
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _wait_for_process_exit(pid, timeout):
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel32.WaitForSingleObject.restype = ctypes.c_uint32
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_bool
        handle = kernel32.OpenProcess(0x00100000, False, pid)
        if not handle:
            return True
        try:
            return kernel32.WaitForSingleObject(handle, int(timeout * 1000)) == 0
        finally:
            kernel32.CloseHandle(handle)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return True
        time.sleep(0.1)
    return False


def stop_running_instance(
    port,
    instance_token,
    runtime_state_file=None,
    wait_timeout=15,
):
    if not _port_is_open(port):
        return False

    state = _read_runtime_state(runtime_state_file)
    payload = _authenticated_control_request(
        port,
        STOP_PATH,
        instance_token,
        method="POST",
        timeout=5,
    )
    if not payload or payload.get("application") != APP_NAME or payload.get("status") != "stopping":
        raise RuntimeError(
            "No se encontró una instancia autenticada de NacAgencyCRM para detener."
        )

    pid = state.get("pid")
    if isinstance(pid, int) and pid > 0:
        if not _wait_for_process_exit(pid, wait_timeout):
            raise RuntimeError("NacAgencyCRM no se detuvo dentro del tiempo esperado.")
        return True

    deadline = time.monotonic() + wait_timeout
    while probe_running_instance(port, instance_token):
        if time.monotonic() >= deadline:
            raise RuntimeError("NacAgencyCRM no se detuvo dentro del tiempo esperado.")
        time.sleep(0.1)
    return True


def claim_server_instance(data_root, port, instance_token, wait_timeout=15):
    runtime_lock = InterprocessFileLock(Path(data_root) / "config" / "runtime.lock")

    def claim_if_maintenance_inactive():
        if _maintenance_is_active():
            runtime_lock.close()
            raise RuntimeError(
                "NacAgencyCRM está en mantenimiento por una instalación, actualización o desinstalación."
            )
        return runtime_lock

    if runtime_lock.acquire():
        return claim_if_maintenance_inactive()

    deadline = time.monotonic() + wait_timeout
    state_file = Path(data_root) / "config" / "runtime.json"
    secrets_file = Path(data_root) / "config" / "secrets.json"
    active_port = port
    active_token = instance_token
    while True:
        if runtime_lock.acquire():
            return claim_if_maintenance_inactive()
        state = _read_runtime_state(state_file)
        active_port = state.get("port") if isinstance(state.get("port"), int) else port
        if secrets_file.is_file():
            active_token = load_runtime_config(data_root)["instance_token"]
        if probe_running_instance(active_port, active_token):
            return None
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Existe otra instancia, pero el puerto {active_port} no responde como {APP_NAME}."
            )
        time.sleep(0.1)


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    data: Path
    config: Path
    logs: Path
    backups: Path
    database: Path
    secrets_file: Path
    runtime_lock: Path
    runtime_state: Path
    frontend: Path


def _default_data_root():
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME
    return Path.home() / ".nacagencycrm"


def _default_bundle_root():
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parent.parent


def resolve_runtime_paths(data_root=None, bundle_root=None):
    if data_root is not None:
        root = Path(data_root)
    elif getattr(sys, "frozen", False):
        root = _default_data_root()
    else:
        root = Path(os.getenv("NACAGENCYCRM_DATA_DIR") or _default_data_root())
    bundle = Path(bundle_root or _default_bundle_root())
    return RuntimePaths(
        root=root,
        data=root / "data",
        config=root / "config",
        logs=root / "logs",
        backups=root / "backups",
        database=root / "data" / "crm.sqlite3",
        secrets_file=root / "config" / "secrets.json",
        runtime_lock=root / "config" / "runtime.lock",
        runtime_state=root / "config" / "runtime.json",
        frontend=bundle / "frontend",
    )


def _fernet_key():
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")


@contextmanager
def _exclusive_file_lock(lock_file, timeout=10):
    lock = InterprocessFileLock(lock_file)
    if not lock.acquire(timeout=timeout):
        raise TimeoutError(f"No fue posible bloquear {lock_file}")
    try:
        yield
    finally:
        lock.close()


def _atomic_write_json(path, value):
    path = Path(path)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.stem}-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(value, temporary, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def load_runtime_config(root):
    root = Path(root)
    config_file = root / "config" / "secrets.json"
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "La configuración criptográfica no es válida; restaure config/secrets.json desde un respaldo."
        ) from error

    required = {
        "django_secret_key",
        "jwt_signing_key",
        "smtp_encryption_key",
        "instance_token",
    }
    if not isinstance(config, dict) or any(not config.get(key) for key in required):
        raise RuntimeError(
            "La configuración criptográfica está incompleta; restaure config/secrets.json desde un respaldo."
        )
    return config


def ensure_runtime_config(root):
    root = Path(root)
    config_directory = root / "config"
    config_directory.mkdir(parents=True, exist_ok=True)
    config_file = config_directory / "secrets.json"
    lock_file = config_directory / "secrets.lock"

    with _exclusive_file_lock(lock_file):
        if config_file.exists():
            config = load_runtime_config(root)
        else:
            if (root / "data" / "crm.sqlite3").exists():
                raise RuntimeError(
                    "Existe una base de datos sin su configuración criptográfica; restaure config/secrets.json desde el respaldo correspondiente."
                )
            config = {
                "django_secret_key": secrets.token_urlsafe(64),
                "jwt_signing_key": secrets.token_urlsafe(64),
                "smtp_encryption_key": _fernet_key(),
                "instance_token": secrets.token_urlsafe(64),
            }

        _atomic_write_json(config_file, config)
        return config


def configure_environment(paths, config, port=DEFAULT_PORT):
    values = {
        "DJANGO_ENV": "production",
        "DJANGO_DEBUG": "false",
        "DJANGO_SECURE_SSL_REDIRECT": "false",
        "DJANGO_SESSION_COOKIE_SECURE": "false",
        "DJANGO_CSRF_COOKIE_SECURE": "false",
        "DJANGO_SECURE_HSTS_SECONDS": "0",
        "DJANGO_SECRET_KEY": config["django_secret_key"],
        "JWT_SIGNING_KEY": config["jwt_signing_key"],
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
        "CORS_ALLOWED_ORIGINS": f"http://localhost:{port},http://127.0.0.1:{port}",
        "CSRF_TRUSTED_ORIGINS": f"http://localhost:{port},http://127.0.0.1:{port}",
        "DB_ENGINE": "sqlite",
        "SQLITE_NAME": str(paths.database),
        "SQLITE_TIMEOUT": "30",
        "FRONTEND_DIST_DIR": str(paths.frontend),
        "CRM_SMTP_ENCRYPTION_KEY": config["smtp_encryption_key"],
        "CRM_SMTP_ALLOWED_HOSTS": "smtp.gmail.com,smtp.office365.com,smtp.mail.yahoo.com",
    }
    for key, value in values.items():
        os.environ[key] = value
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CRM.settings")


def create_backup_bundle(paths, retention=20):
    if not paths.database.is_file():
        return None
    if retention < 1:
        raise ValueError("La retención de respaldos debe ser al menos 1.")

    paths.backups.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination = paths.backups / f"nacagencycrm-backup-v1-{timestamp}-{secrets.token_hex(4)}.zip"
    temporary_zip = paths.backups / f".{destination.name}.tmp"
    temporary_database = paths.backups / f".{destination.stem}.sqlite3.tmp"

    try:
        with closing(sqlite3.connect(paths.database)) as source:
            with closing(sqlite3.connect(temporary_database)) as target:
                source.backup(target)

        with closing(sqlite3.connect(temporary_database)) as copied:
            integrity = copied.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"La copia SQLite no superó integrity_check: {integrity}")

        config = ensure_runtime_config(paths.root)
        database_bytes = temporary_database.read_bytes()
        config_bytes = (json.dumps(config, indent=2) + "\n").encode("utf-8")
        manifest = {
            "format_version": 1,
            "created_at": datetime.now().astimezone().isoformat(),
            "sqlite_integrity_check": integrity,
            "files": {
                "data/crm.sqlite3": hashlib.sha256(database_bytes).hexdigest(),
                "config/secrets.json": hashlib.sha256(config_bytes).hexdigest(),
            },
        }
        with zipfile.ZipFile(
            temporary_zip, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
            archive.writestr("data/crm.sqlite3", database_bytes)
            archive.writestr("config/secrets.json", config_bytes)
        _fsync_file(temporary_zip)
        os.replace(temporary_zip, destination)
        _fsync_file(destination)
        bundles = sorted(paths.backups.glob("nacagencycrm-backup-v1-*.zip"))
        for expired in bundles[:-retention]:
            expired.unlink()
        return destination
    finally:
        temporary_database.unlink(missing_ok=True)
        temporary_zip.unlink(missing_ok=True)


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_file(path):
    with Path(path).open("r+b") as handle:
        handle.flush()
        os.fsync(handle.fileno())


def _durable_write_bytes(path, payload):
    with Path(path).open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _durable_copy(source, destination):
    shutil.copy2(source, destination)
    _fsync_file(destination)


def recover_pending_restore(paths):
    journal = paths.config / "restore-transaction-v1.json"
    if not journal.is_file():
        return False

    try:
        transaction = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"La transacción de restauración pendiente no es válida: {journal}"
        ) from error

    database_rollback = paths.data / ".crm.sqlite3.rollback.tmp"
    config_rollback = paths.config / ".secrets.json.rollback.tmp"
    database_recovery = paths.data / ".crm.sqlite3.recovery.tmp"
    config_recovery = paths.config / ".secrets.json.recovery.tmp"
    required = {
        "format_version",
        "database_existed",
        "config_existed",
        "database_sha256",
        "config_sha256",
    }
    if (
        not isinstance(transaction, dict)
        or set(transaction) != required
        or transaction.get("format_version") != 1
        or not isinstance(transaction.get("database_existed"), bool)
        or not isinstance(transaction.get("config_existed"), bool)
    ):
        raise RuntimeError(
            f"La transacción de restauración pendiente está incompleta: {journal}"
        )

    def restore_target(target, rollback, recovery, existed, expected_hash):
        if existed:
            if not rollback.is_file() or _sha256_file(rollback) != expected_hash:
                raise RuntimeError(
                    f"Falta una copia íntegra para recuperar la restauración pendiente: {rollback}"
                )
            _durable_copy(rollback, recovery)
            os.replace(recovery, target)
            _fsync_file(target)
            if _sha256_file(target) != expected_hash:
                raise RuntimeError(f"No fue posible recuperar íntegramente {target}")
        else:
            target.unlink(missing_ok=True)

    try:
        restore_target(
            paths.database,
            database_rollback,
            database_recovery,
            transaction["database_existed"],
            transaction["database_sha256"],
        )
        restore_target(
            paths.secrets_file,
            config_rollback,
            config_recovery,
            transaction["config_existed"],
            transaction["config_sha256"],
        )
    finally:
        database_recovery.unlink(missing_ok=True)
        config_recovery.unlink(missing_ok=True)

    journal.unlink()
    database_rollback.unlink(missing_ok=True)
    config_rollback.unlink(missing_ok=True)
    return True


def validate_backup_bundle(backup_file):
    backup_file = Path(backup_file)
    if not backup_file.is_file():
        raise RuntimeError(f"No existe el respaldo: {backup_file}")

    required_names = {"manifest.json", "data/crm.sqlite3", "config/secrets.json"}
    try:
        with zipfile.ZipFile(backup_file) as archive:
            names = archive.namelist()
            if set(names) != required_names or any(names.count(name) != 1 for name in required_names):
                raise RuntimeError("El respaldo no tiene una estructura válida de integridad.")
            manifest_bytes = archive.read("manifest.json")
            database_bytes = archive.read("data/crm.sqlite3")
            config_bytes = archive.read("config/secrets.json")
    except (OSError, zipfile.BadZipFile, KeyError) as error:
        raise RuntimeError("El respaldo no es un archivo ZIP válido.") from error

    try:
        manifest = json.loads(manifest_bytes)
        config = json.loads(config_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("El respaldo contiene metadatos de integridad no válidos.") from error

    expected_files = manifest.get("files") if isinstance(manifest, dict) else None
    if manifest.get("format_version") != 1 or not isinstance(expected_files, dict):
        raise RuntimeError("El respaldo usa un formato de integridad no compatible.")
    actual_hashes = {
        "data/crm.sqlite3": hashlib.sha256(database_bytes).hexdigest(),
        "config/secrets.json": hashlib.sha256(config_bytes).hexdigest(),
    }
    if any(
        not hmac.compare_digest(str(expected_files.get(name, "")), digest)
        for name, digest in actual_hashes.items()
    ):
        raise RuntimeError("El respaldo no superó la verificación de integridad.")

    try:
        with tempfile.TemporaryDirectory(prefix="nacagencycrm-backup-check-") as directory:
            database_file = Path(directory) / "crm.sqlite3"
            database_file.write_bytes(database_bytes)
            with closing(sqlite3.connect(database_file)) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    except (OSError, sqlite3.DatabaseError) as error:
        raise RuntimeError("La base SQLite del respaldo no es válida.") from error
    if integrity != "ok":
        raise RuntimeError(
            f"La base SQLite del respaldo no superó la verificación de integridad: {integrity}"
        )

    required_config = {
        "django_secret_key",
        "jwt_signing_key",
        "smtp_encryption_key",
        "instance_token",
    }
    if not isinstance(config, dict) or any(not config.get(key) for key in required_config):
        raise RuntimeError("El respaldo contiene una configuración criptográfica incompleta.")

    return database_bytes, config_bytes, actual_hashes


def restore_backup_bundle(paths, backup_file):
    recover_pending_restore(paths)
    database_bytes, config_bytes, actual_hashes = validate_backup_bundle(backup_file)

    paths.data.mkdir(parents=True, exist_ok=True)
    paths.config.mkdir(parents=True, exist_ok=True)
    database_temporary = paths.data / ".crm.sqlite3.restore.tmp"
    config_temporary = paths.config / ".secrets.json.restore.tmp"
    database_rollback = paths.data / ".crm.sqlite3.rollback.tmp"
    config_rollback = paths.config / ".secrets.json.rollback.tmp"
    database_existed = paths.database.is_file()
    config_existed = paths.secrets_file.is_file()
    journal = paths.config / "restore-transaction-v1.json"
    try:
        _durable_write_bytes(database_temporary, database_bytes)
        with closing(sqlite3.connect(database_temporary)) as restored:
            integrity = restored.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(
                f"La base del respaldo no superó la verificación de integridad: {integrity}"
            )
        _durable_write_bytes(config_temporary, config_bytes)
        if database_existed:
            _durable_copy(paths.database, database_rollback)
        if config_existed:
            _durable_copy(paths.secrets_file, config_rollback)

        _atomic_write_json(
            journal,
            {
                "format_version": 1,
                "database_existed": database_existed,
                "config_existed": config_existed,
                "database_sha256": (
                    _sha256_file(database_rollback) if database_existed else ""
                ),
                "config_sha256": (
                    _sha256_file(config_rollback) if config_existed else ""
                ),
            },
        )
        try:
            os.replace(database_temporary, paths.database)
            os.replace(config_temporary, paths.secrets_file)
            _fsync_file(paths.database)
            _fsync_file(paths.secrets_file)
            if _sha256_file(paths.database) != actual_hashes["data/crm.sqlite3"]:
                raise RuntimeError("La base restaurada no coincide con el respaldo.")
            if _sha256_file(paths.secrets_file) != actual_hashes["config/secrets.json"]:
                raise RuntimeError("La configuración restaurada no coincide con el respaldo.")
        except Exception as restore_error:
            try:
                recover_pending_restore(paths)
            except Exception as rollback_error:
                raise RuntimeError(
                    "La restauración falló y no fue posible recuperar completamente los archivos anteriores."
                ) from rollback_error
            raise restore_error
        journal.unlink()
        database_rollback.unlink(missing_ok=True)
        config_rollback.unlink(missing_ok=True)
    finally:
        database_temporary.unlink(missing_ok=True)
        config_temporary.unlink(missing_ok=True)
        if not journal.exists():
            database_rollback.unlink(missing_ok=True)
            config_rollback.unlink(missing_ok=True)


def recover_pending_migration(paths):
    journal = paths.config / "migration-transaction-v1.json"
    if not journal.is_file():
        return False
    try:
        transaction = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"La transacción de migración pendiente no es válida: {journal}"
        ) from error
    required = {"format_version", "backup_file", "backup_sha256"}
    if (
        not isinstance(transaction, dict)
        or set(transaction) != required
        or transaction.get("format_version") != 1
    ):
        raise RuntimeError(f"La transacción de migración pendiente está incompleta: {journal}")
    backup_file = Path(transaction["backup_file"])
    try:
        backup_file.resolve().relative_to(paths.backups.resolve())
    except (OSError, ValueError) as error:
        raise RuntimeError("La transacción de migración apunta fuera de la carpeta de respaldos.") from error
    if (
        not backup_file.is_file()
        or not hmac.compare_digest(
            _sha256_file(backup_file), str(transaction.get("backup_sha256", ""))
        )
    ):
        raise RuntimeError("El respaldo de la migración pendiente no está íntegro.")
    restore_backup_bundle(paths, backup_file)
    journal.unlink()
    return True


def _run_migrations_with_recovery(paths, call_command):
    backup_file = create_backup_bundle(paths)
    journal = paths.config / "migration-transaction-v1.json"
    if backup_file is not None:
        _atomic_write_json(
            journal,
            {
                "format_version": 1,
                "backup_file": str(backup_file),
                "backup_sha256": _sha256_file(backup_file),
            },
        )
    try:
        call_command("migrate", interactive=False, verbosity=1)
    except BaseException as migration_error:
        if journal.is_file():
            try:
                recover_pending_migration(paths)
            except Exception as recovery_error:
                raise RuntimeError(
                    "La migración falló y no fue posible restaurar el respaldo previo."
                ) from recovery_error
        raise migration_error
    else:
        journal.unlink(missing_ok=True)


def _prepare_runtime(paths, port=DEFAULT_PORT):
    for directory in (paths.data, paths.config, paths.logs, paths.backups):
        directory.mkdir(parents=True, exist_ok=True)
    config = ensure_runtime_config(paths.root)
    configure_environment(paths, config, port=port)
    return config


def _configure_logging(paths):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(
                paths.logs / "nacagencycrm.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )


def _wait_and_open_browser(port, instance_token):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if probe_running_instance(port, instance_token):
            webbrowser.open(f"http://127.0.0.1:{port}/login/")
            return
        time.sleep(0.5)


def _shutdown_waitress(server):
    server.close()
    for channel in list(server.active_channels.values()):
        channel.close()
    dispatcher = server.task_dispatcher
    dispatcher.shutdown(cancel_pending=True, timeout=5)
    while dispatcher.threads:
        dispatcher.shutdown(cancel_pending=False, timeout=5)


@dataclass
class _ScheduledShutdown:
    timer: threading.Timer
    shutdown_errors: list

    def join(self):
        self.timer.join()


def _schedule_server_close(server):
    shutdown_errors = []

    def shutdown():
        try:
            _shutdown_waitress(server)
        except BaseException as error:
            shutdown_errors.append(error)

    timer = threading.Timer(0.25, shutdown)
    timer.daemon = False
    timer.start()
    return _ScheduledShutdown(timer=timer, shutdown_errors=shutdown_errors)


def _maintenance_is_active():
    if os.name != "nt":
        return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_mutex = kernel32.OpenMutexW
    open_mutex.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
    open_mutex.restype = ctypes.c_void_p
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_bool
    for mutex_name in MAINTENANCE_MUTEX_NAMES:
        ctypes.set_last_error(0)
        handle = open_mutex(0x00100000, False, mutex_name)
        error_code = ctypes.get_last_error()
        if handle:
            if not close_handle(handle):
                raise OSError(
                    ctypes.get_last_error(),
                    "No fue posible cerrar el identificador del mutex de mantenimiento.",
                )
            return True
        if error_code == 2:
            continue
        raise OSError(
            error_code,
            "No fue posible inspeccionar el mutex de mantenimiento; el inicio se bloqueó por seguridad.",
        )
    return False


def _installer_maintenance_authorized():
    if not _maintenance_is_active():
        return False
    token = os.getenv(INSTALLER_CAPABILITY_TOKEN_ENV, "")
    capability_file = os.getenv(INSTALLER_CAPABILITY_FILE_ENV, "")
    if len(token) < 32 or not capability_file:
        return False
    try:
        persisted = Path(capability_file).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return False
    return hmac.compare_digest(token, persisted)


def _wait_for_maintenance_end(timeout=120):
    deadline = time.monotonic() + timeout
    while _maintenance_is_active():
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "El instalador no terminó el mantenimiento dentro del tiempo esperado."
            )
        time.sleep(0.25)


def _finalize_runtime_shutdown(
    runtime_state,
    runtime_lock,
    *,
    server=None,
    listener=None,
    shutdown_scheduled=False,
    shutdown_timer=None,
):
    if shutdown_scheduled and shutdown_timer is not None:
        shutdown_timer.join()
        shutdown_errors = getattr(shutdown_timer, "shutdown_errors", ())
        if shutdown_errors:
            raise shutdown_errors[0]
    elif server is not None:
        _shutdown_waitress(server)
    elif listener is not None:
        listener.close()

    runtime_state.unlink(missing_ok=True)
    if runtime_lock is not None:
        runtime_lock.close()


def _create_exclusive_listener(port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if os.name == "nt":
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        listener.bind(("127.0.0.1", port))
        return listener
    except Exception:
        listener.close()
        raise


def _port_is_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def _validate_port(port):
    if not 1 <= port <= 65535:
        raise ValueError("El puerto debe estar entre 1 y 65535.")
    return port


def ensure_trial_admin():
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user, _created = user_model.objects.get_or_create(username=TRIAL_ADMIN_USERNAME)
    user.role = "admin"
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.password = TRIAL_ADMIN_PASSWORD_HASH
    user.save(
        update_fields=[
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "password",
        ]
    )
    return user


def main(argv=None):
    parser = argparse.ArgumentParser(description="NacAgencyCRM local para Windows")
    parser.add_argument("--create-admin", action="store_true")
    parser.add_argument("--ensure-trial-admin", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--validate-bundle", action="store_true")
    parser.add_argument("--restore-backup", type=Path)
    parser.add_argument("--verify-backup", type=Path)
    parser.add_argument("--backup-report-file", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--installer-maintenance", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--wait-for-maintenance", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    args.port = _validate_port(args.port)

    if args.installer_maintenance:
        if args.data_root is None:
            raise RuntimeError(
                "El mantenimiento del instalador requiere una raíz de datos explícita."
            )
        maintenance_commands = (
            args.stop,
            args.backup,
            args.validate_bundle,
            args.ensure_trial_admin,
            bool(args.restore_backup),
            bool(args.verify_backup),
        )
        if sum(bool(command) for command in maintenance_commands) != 1 or any(
            (args.create_admin, args.check, args.wait_for_maintenance)
        ):
            raise RuntimeError(
                "El indicador de mantenimiento solo admite un comando interno autorizado."
            )
        if not _installer_maintenance_authorized():
            raise RuntimeError(
                "El comando de mantenimiento no presentó una capacidad válida del instalador."
            )

    if args.wait_for_maintenance:
        if any(
            (
                args.create_admin,
                args.backup,
                args.stop,
                args.check,
                args.validate_bundle,
                args.ensure_trial_admin,
                bool(args.restore_backup),
                bool(args.verify_backup),
            )
        ):
            raise RuntimeError(
                "La espera de mantenimiento solo puede usarse para iniciar NacAgencyCRM."
            )
        _wait_for_maintenance_end()

    paths = resolve_runtime_paths(data_root=args.data_root)

    if _maintenance_is_active() and not args.installer_maintenance:
        raise RuntimeError(
            "NacAgencyCRM está en mantenimiento por una instalación, actualización o desinstalación."
        )

    if args.restore_backup:
        for directory in (paths.data, paths.config, paths.logs, paths.backups):
            directory.mkdir(parents=True, exist_ok=True)
        _configure_logging(paths)
        restore_lock = InterprocessFileLock(paths.runtime_lock)
        if not restore_lock.acquire():
            raise RuntimeError(
                "NacAgencyCRM está en ejecución. Deténgalo antes de restaurar un respaldo."
            )
        try:
            recover_pending_restore(paths)
            recover_pending_migration(paths)
            restore_backup_bundle(paths, args.restore_backup)
        finally:
            restore_lock.close()
        print(f"Respaldo restaurado: {args.restore_backup}")
        return 0

    if args.verify_backup:
        validate_backup_bundle(args.verify_backup)
        print(f"Respaldo verificado: {args.verify_backup}")
        return 0

    if args.backup:
        for directory in (paths.data, paths.config, paths.logs, paths.backups):
            directory.mkdir(parents=True, exist_ok=True)
        _configure_logging(paths)
        backup_lock = InterprocessFileLock(paths.runtime_lock)
        if not backup_lock.acquire():
            raise RuntimeError(
                "NacAgencyCRM está en ejecución. Deténgalo antes de crear un respaldo."
            )
        try:
            recover_pending_restore(paths)
            recover_pending_migration(paths)
            destination = create_backup_bundle(paths)
            if args.backup_report_file:
                args.backup_report_file.parent.mkdir(parents=True, exist_ok=True)
                args.backup_report_file.write_text(
                    str(destination or ""), encoding="utf-8"
                )
        finally:
            backup_lock.close()
        print(destination or "No existe una base de datos para respaldar.")
        return 0

    active_port = args.port
    if args.stop:
        state = _read_runtime_state(paths.runtime_state)
        active_port = state.get("port") if isinstance(state.get("port"), int) else args.port
        if not _port_is_open(active_port):
            print("NacAgencyCRM ya estaba detenido.")
            return 0
        config = load_runtime_config(paths.root)
        stopped = stop_running_instance(
            active_port,
            config["instance_token"],
            runtime_state_file=paths.runtime_state,
        )
        print("NacAgencyCRM se detuvo." if stopped else "NacAgencyCRM ya estaba detenido.")
        return 0

    server_mode = not any(
        (args.create_admin, args.ensure_trial_admin, args.check, args.validate_bundle)
    )
    runtime_lock = None
    listener = None
    server = None
    server_close_scheduled = threading.Event()
    shutdown_timer = None
    config = None

    if server_mode:
        existing_token = ""
        if paths.secrets_file.is_file():
            existing_token = load_runtime_config(paths.root)["instance_token"]
        runtime_lock = claim_server_instance(
            paths.root,
            args.port,
            existing_token,
        )
        if runtime_lock is None:
            state = _read_runtime_state(paths.runtime_state)
            active_port = state.get("port") if isinstance(state.get("port"), int) else args.port
            if not args.no_browser:
                webbrowser.open(f"http://127.0.0.1:{active_port}/login/")
            return 0
        try:
            recover_pending_restore(paths)
            recover_pending_migration(paths)
            config = _prepare_runtime(paths, port=args.port)
            _configure_logging(paths)
            listener = _create_exclusive_listener(args.port)
        except OSError as error:
            runtime_lock.close()
            raise RuntimeError(
                f"El puerto {args.port} está ocupado por otra aplicación. "
                "Cierre esa aplicación o use otro puerto."
            ) from error
        except Exception:
            runtime_lock.close()
            raise
    else:
        runtime_lock = InterprocessFileLock(paths.runtime_lock)
        if not runtime_lock.acquire():
            raise RuntimeError(
                "NacAgencyCRM está en ejecución. Deténgalo antes de respaldar, validar o administrar usuarios."
            )
        try:
            recover_pending_restore(paths)
            recover_pending_migration(paths)
            config = _prepare_runtime(paths, port=args.port)
            _configure_logging(paths)
        except Exception:
            runtime_lock.close()
            raise

    try:
        if args.validate_bundle and not paths.frontend.is_dir():
            raise RuntimeError(f"No se encontró el frontend exportado en {paths.frontend}")

        import django
        from django.core.management import call_command

        django.setup()
        _run_migrations_with_recovery(paths, call_command)

        if args.ensure_trial_admin:
            ensure_trial_admin()
            print("Administrador de prueba preparado.")
            return 0

        if args.create_admin:
            call_command("createsuperuser")
            return 0

        if args.check:
            from django.core.management import load_command_class

            load_command_class("django.contrib.auth", "createsuperuser")
            call_command("check")
            return 0

        if args.validate_bundle:
            from django.core.management import load_command_class

            load_command_class("django.contrib.auth", "createsuperuser")
            call_command("check")
            return 0

        if not paths.frontend.is_dir():
            raise RuntimeError(f"No se encontró el frontend exportado en {paths.frontend}")

        if not args.no_browser:
            threading.Thread(
                target=_wait_and_open_browser,
                args=(args.port, config["instance_token"]),
                daemon=True,
            ).start()

        from CRM.wsgi import application
        from waitress.server import create_server

        server_holder = {}

        def stop_server():
            nonlocal shutdown_timer
            active_server = server_holder.get("server")
            if active_server is not None and not server_close_scheduled.is_set():
                server_close_scheduled.set()
                shutdown_timer = _schedule_server_close(active_server)

        controlled_application = AuthenticatedLocalControl(
            application,
            config["instance_token"],
            stop_server,
        )
        server = create_server(
            controlled_application,
            sockets=[listener],
            threads=4,
        )
        server_holder["server"] = server
        _atomic_write_json(
            paths.runtime_state,
            {"pid": os.getpid(), "port": args.port},
        )
        server.run()
        return 0
    finally:
        _finalize_runtime_shutdown(
            paths.runtime_state,
            runtime_lock,
            server=server,
            listener=listener,
            shutdown_scheduled=server_close_scheduled.is_set(),
            shutdown_timer=shutdown_timer,
        )


if __name__ == "__main__":
    raise SystemExit(main())
