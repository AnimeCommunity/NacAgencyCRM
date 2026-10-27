import hashlib
import json
import os
import socket
import sqlite3
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest import skipUnless
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from windows_runtime import (
    APP_NAME,
    MAINTENANCE_MUTEX_NAMES,
    AuthenticatedLocalControl,
    _create_exclusive_listener,
    _exclusive_file_lock,
    _finalize_runtime_shutdown,
    _maintenance_is_active,
    _run_migrations_with_recovery,
    _schedule_server_close,
    _shutdown_waitress,
    _validate_port,
    _wait_for_maintenance_end,
    _configure_logging,
    claim_server_instance,
    configure_environment,
    create_backup_bundle,
    ensure_runtime_config,
    probe_running_instance,
    recover_pending_migration,
    resolve_runtime_paths,
    restore_backup_bundle,
    stop_running_instance,
    validate_backup_bundle,
)


class WindowsRuntimeTests(SimpleTestCase):
    def test_default_data_root_is_private_to_the_current_windows_user(self):
        with patch.dict(
            os.environ,
            {"PROGRAMDATA": r"C:\ProgramData", "LOCALAPPDATA": r"C:\Users\Alice\AppData\Local"},
            clear=True,
        ):
            paths = resolve_runtime_paths(bundle_root=Path("bundle"))

        self.assertEqual(
            paths.root,
            Path(r"C:\Users\Alice\AppData\Local") / "NacAgencyCRM",
        )

    def test_frozen_runtime_ignores_inherited_data_root_override(self):
        with (
            patch.dict(
                os.environ,
                {
                    "LOCALAPPDATA": r"C:\Users\Alice\AppData\Local",
                    "NACAGENCYCRM_DATA_DIR": r"C:\AttackerControlled",
                },
                clear=True,
            ),
            patch("windows_runtime.sys.frozen", True, create=True),
        ):
            paths = resolve_runtime_paths(bundle_root=Path("bundle"))

        self.assertEqual(
            paths.root,
            Path(r"C:\Users\Alice\AppData\Local") / "NacAgencyCRM",
        )

    def test_explicit_data_root_is_honored_for_installer_maintenance(self):
        with patch("windows_runtime.sys.frozen", True, create=True):
            paths = resolve_runtime_paths(
                data_root=Path(r"C:\MaintenanceData"), bundle_root=Path("bundle")
            )

        self.assertEqual(paths.root, Path(r"C:\MaintenanceData"))

    def test_port_validation_accepts_only_tcp_port_range(self):
        self.assertEqual(_validate_port(1), 1)
        self.assertEqual(_validate_port(65535), 65535)
        for invalid in (0, -1, 65536):
            with self.subTest(port=invalid):
                with self.assertRaises(ValueError):
                    _validate_port(invalid)

    def test_runtime_config_is_persistent_and_uses_distinct_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            first = ensure_runtime_config(root)
            second = ensure_runtime_config(root)

            self.assertEqual(first, second)
            self.assertNotEqual(first["django_secret_key"], first["jwt_signing_key"])
            self.assertGreaterEqual(len(first["django_secret_key"]), 50)
            self.assertGreaterEqual(len(first["jwt_signing_key"]), 50)
            self.assertGreaterEqual(len(first["instance_token"]), 50)
            self.assertNotIn(first["instance_token"], {first["django_secret_key"], first["jwt_signing_key"]})
            self.assertTrue((root / "config" / "secrets.json").is_file())

    def test_runtime_config_refuses_to_replace_missing_secrets_for_existing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "data" / "crm.sqlite3"
            database.parent.mkdir(parents=True)
            database.write_bytes(b"existing database")

            with self.assertRaisesRegex(RuntimeError, "restaure.*secrets.json"):
                ensure_runtime_config(root)

    def test_runtime_config_creation_is_atomic_under_concurrency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with ThreadPoolExecutor(max_workers=12) as executor:
                configs = list(executor.map(lambda _: ensure_runtime_config(root), range(24)))

            self.assertTrue(all(config == configs[0] for config in configs))
            persisted = json.loads(
                (root / "config" / "secrets.json").read_text(encoding="utf-8")
            )
            self.assertEqual(persisted, configs[0])
            self.assertEqual(list((root / "config").glob("*.tmp")), [])
            self.assertTrue((root / "config" / "secrets.lock").exists())

    def test_file_lock_times_out_while_another_owner_holds_it(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_file = Path(directory) / "runtime.lock"

            with _exclusive_file_lock(lock_file):
                with self.assertRaises(TimeoutError):
                    with _exclusive_file_lock(lock_file, timeout=0):
                        pass

    def test_file_lock_is_os_managed_and_reusable_after_release(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_file = Path(directory) / "runtime.lock"

            with _exclusive_file_lock(lock_file):
                self.assertTrue(lock_file.exists())

            self.assertTrue(lock_file.exists())
            with _exclusive_file_lock(lock_file):
                pass

    def test_configure_environment_uses_local_sqlite_and_frontend_paths(self):
        with tempfile.TemporaryDirectory() as data_directory, tempfile.TemporaryDirectory() as bundle_directory:
            paths = resolve_runtime_paths(Path(data_directory), Path(bundle_directory))
            config = {
                "django_secret_key": "d" * 64,
                "jwt_signing_key": "j" * 64,
                "smtp_encryption_key": "c" * 44,
            }

            with patch.dict(os.environ, {}, clear=True):
                configure_environment(paths, config)

                self.assertEqual(os.environ["DB_ENGINE"], "sqlite")
                self.assertEqual(os.environ["SQLITE_NAME"], str(paths.database))
                self.assertEqual(os.environ["FRONTEND_DIST_DIR"], str(paths.frontend))
                self.assertEqual(os.environ["DJANGO_SECURE_SSL_REDIRECT"], "false")

    def test_backup_bundle_contains_integrity_checked_database_and_matching_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            config = ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.execute("INSERT INTO example VALUES ('ok')")
                connection.commit()

            backup = create_backup_bundle(paths)

            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertEqual(backup.suffix, ".zip")
            with zipfile.ZipFile(backup) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"manifest.json", "data/crm.sqlite3", "config/secrets.json"},
                )
                manifest = json.loads(archive.read("manifest.json"))
                archived_config = json.loads(archive.read("config/secrets.json"))
                extracted_database = Path(directory) / "restored.sqlite3"
                extracted_database.write_bytes(archive.read("data/crm.sqlite3"))

            self.assertEqual(manifest["format_version"], 1)
            self.assertEqual(manifest["sqlite_integrity_check"], "ok")
            self.assertEqual(archived_config, config)
            with closing(sqlite3.connect(extracted_database)) as connection:
                value = connection.execute("SELECT value FROM example").fetchone()[0]
            self.assertEqual(value, "ok")
            self.assertEqual(list(paths.backups.glob("*.tmp")), [])

    def test_backup_verification_rejects_hash_valid_non_sqlite_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.commit()
            backup = create_backup_bundle(paths)
            assert backup is not None

            with zipfile.ZipFile(backup) as source:
                manifest = json.loads(source.read("manifest.json"))
                config_bytes = source.read("config/secrets.json")
            invalid_database = b"not a sqlite database"
            manifest["files"]["data/crm.sqlite3"] = hashlib.sha256(
                invalid_database
            ).hexdigest()
            with zipfile.ZipFile(backup, "w") as destination:
                destination.writestr("manifest.json", json.dumps(manifest))
                destination.writestr("data/crm.sqlite3", invalid_database)
                destination.writestr("config/secrets.json", config_bytes)

            with self.assertRaisesRegex(RuntimeError, "SQLite"):
                validate_backup_bundle(backup)

    def test_failed_migration_restores_the_pre_migration_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.execute("INSERT INTO example VALUES ('before')")
                connection.commit()

            def failing_migrate(*_args, **_kwargs):
                with closing(sqlite3.connect(paths.database)) as connection:
                    connection.execute("UPDATE example SET value = 'partial'")
                    connection.commit()
                raise RuntimeError("simulated migration failure")

            with self.assertRaisesRegex(RuntimeError, "migration failure"):
                _run_migrations_with_recovery(paths, failing_migrate)

            with closing(sqlite3.connect(paths.database)) as connection:
                value = connection.execute("SELECT value FROM example").fetchone()[0]
            self.assertEqual(value, "before")
            self.assertFalse((paths.config / "migration-transaction-v1.json").exists())

    def test_pending_migration_is_recovered_after_process_termination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.execute("INSERT INTO example VALUES ('before')")
                connection.commit()
            backup = create_backup_bundle(paths)
            assert backup is not None
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("UPDATE example SET value = 'partial'")
                connection.commit()
            journal = paths.config / "migration-transaction-v1.json"
            journal.write_text(
                json.dumps(
                    {
                        "format_version": 1,
                        "backup_file": str(backup),
                        "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )

            self.assertTrue(recover_pending_migration(paths))

            with closing(sqlite3.connect(paths.database)) as connection:
                value = connection.execute("SELECT value FROM example").fetchone()[0]
            self.assertEqual(value, "before")
            self.assertFalse(journal.exists())

    def test_restore_backup_replaces_database_and_cryptographic_config_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            original_config = ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.execute("INSERT INTO example VALUES ('original')")
                connection.commit()
            backup = create_backup_bundle(paths)
            assert backup is not None

            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("UPDATE example SET value = 'modified'")
                connection.commit()
            paths.secrets_file.write_text(
                json.dumps({"invalid": "replacement"}), encoding="utf-8"
            )

            restore_backup_bundle(paths, backup)

            with closing(sqlite3.connect(paths.database)) as connection:
                value = connection.execute("SELECT value FROM example").fetchone()[0]
            restored_config = json.loads(paths.secrets_file.read_text(encoding="utf-8"))
            self.assertEqual(value, "original")
            self.assertEqual(restored_config, original_config)
            self.assertEqual(list(root.rglob("*.restore.tmp")), [])

    def test_restore_rolls_back_database_if_replacing_secrets_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            original_config = ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.execute("INSERT INTO example VALUES ('backup')")
                connection.commit()
            backup = create_backup_bundle(paths)
            assert backup is not None

            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("UPDATE example SET value = 'live'")
                connection.commit()
            live_config = {**original_config, "instance_token": "live-instance-token"}
            paths.secrets_file.write_text(json.dumps(live_config), encoding="utf-8")
            real_replace = os.replace

            def fail_secrets_replace(source, destination):
                if Path(destination) == paths.secrets_file and str(source).endswith(
                    ".restore.tmp"
                ):
                    raise OSError("simulated secrets replace failure")
                return real_replace(source, destination)

            with (
                patch("windows_runtime.os.replace", side_effect=fail_secrets_replace),
                self.assertRaisesRegex(OSError, "secrets replace failure"),
            ):
                restore_backup_bundle(paths, backup)

            with closing(sqlite3.connect(paths.database)) as connection:
                value = connection.execute("SELECT value FROM example").fetchone()[0]
            self.assertEqual(value, "live")
            self.assertEqual(
                json.loads(paths.secrets_file.read_text(encoding="utf-8")),
                live_config,
            )
            self.assertEqual(list(root.rglob("*.restore.tmp")), [])
            self.assertEqual(list(root.rglob("*.rollback.tmp")), [])

    def test_restore_recovers_previous_pair_after_interruption_between_replacements(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            backup_config = ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.execute("INSERT INTO example VALUES ('backup')")
                connection.commit()
            backup = create_backup_bundle(paths)
            assert backup is not None

            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("UPDATE example SET value = 'live'")
                connection.commit()
            live_config = {**backup_config, "instance_token": "live-instance-token"}
            paths.secrets_file.write_text(json.dumps(live_config), encoding="utf-8")
            real_replace = os.replace

            def terminate_after_database_replace(source, destination):
                result = real_replace(source, destination)
                if Path(destination) == paths.database and str(source).endswith(
                    ".restore.tmp"
                ):
                    raise SystemExit("simulated process termination")
                return result

            with (
                patch("windows_runtime.os.replace", side_effect=terminate_after_database_replace),
                self.assertRaisesRegex(SystemExit, "process termination"),
            ):
                restore_backup_bundle(paths, backup)

            journal = paths.config / "restore-transaction-v1.json"
            self.assertTrue(journal.is_file())

            import windows_runtime

            windows_runtime.recover_pending_restore(paths)

            with closing(sqlite3.connect(paths.database)) as connection:
                value = connection.execute("SELECT value FROM example").fetchone()[0]
            self.assertEqual(value, "live")
            self.assertEqual(
                json.loads(paths.secrets_file.read_text(encoding="utf-8")),
                live_config,
            )
            self.assertFalse(journal.exists())
            self.assertEqual(list(root.rglob("*.rollback.tmp")), [])

    def test_restore_rejects_a_tampered_bundle_without_changing_live_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            original_config = ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.execute("INSERT INTO example VALUES ('live')")
                connection.commit()
            backup = create_backup_bundle(paths)
            assert backup is not None
            with zipfile.ZipFile(backup) as archive:
                manifest_bytes = archive.read("manifest.json")
                config_bytes = archive.read("config/secrets.json")
            with zipfile.ZipFile(backup, mode="w") as archive:
                archive.writestr("manifest.json", manifest_bytes)
                archive.writestr("data/crm.sqlite3", b"tampered")
                archive.writestr("config/secrets.json", config_bytes)

            with self.assertRaisesRegex(RuntimeError, "integridad"):
                restore_backup_bundle(paths, backup)

            with closing(sqlite3.connect(paths.database)) as connection:
                value = connection.execute("SELECT value FROM example").fetchone()[0]
            self.assertEqual(value, "live")
            self.assertEqual(
                json.loads(paths.secrets_file.read_text(encoding="utf-8")),
                original_config,
            )

    def test_backup_retention_keeps_only_the_newest_bundles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.commit()
            paths.backups.mkdir(parents=True)
            for index in range(5):
                (paths.backups / f"nacagencycrm-backup-v1-20000101-00000{index}-000000-old.zip").write_bytes(
                    b"old"
                )

            newest = create_backup_bundle(paths, retention=3)

            bundles = sorted(paths.backups.glob("nacagencycrm-backup-v1-*.zip"))
            self.assertEqual(len(bundles), 3)
            self.assertIn(newest, bundles)
            self.assertEqual(
                sum("000000-old" in path.name for path in bundles),
                2,
            )

    def test_logging_uses_bounded_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = resolve_runtime_paths(directory, Path(directory) / "bundle")
            paths.logs.mkdir(parents=True)

            with patch("windows_runtime.logging.basicConfig") as basic_config:
                _configure_logging(paths)

            file_handler = basic_config.call_args.kwargs["handlers"][0]
            try:
                self.assertIsInstance(file_handler, RotatingFileHandler)
                self.assertGreater(file_handler.maxBytes, 0)
                self.assertGreaterEqual(file_handler.backupCount, 3)
            finally:
                file_handler.close()

    def test_health_endpoint_requires_instance_token_and_identifies_application(self):
        control = AuthenticatedLocalControl(
            lambda environ, start_response: [b"fallback"],
            instance_token="expected-token",
            stop_callback=Mock(),
        )

        def request(token):
            captured = {}

            def start_response(status, headers):
                captured["status"] = status
                captured["headers"] = headers

            environ = {
                "PATH_INFO": "/__nacagencycrm__/health",
                "REQUEST_METHOD": "GET",
            }
            if token is not None:
                environ["HTTP_X_NACAGENCYCRM_INSTANCE_TOKEN"] = token
            response = control(environ, start_response)
            body = b"".join(response)
            if hasattr(response, "close"):
                response.close()
            return captured["status"], json.loads(body)

        forbidden_status, _ = request("wrong-token")
        ok_status, payload = request("expected-token")

        self.assertTrue(forbidden_status.startswith("403"))
        self.assertTrue(ok_status.startswith("200"))
        self.assertEqual(payload["application"], APP_NAME)
        self.assertEqual(payload["status"], "ok")

    def test_stop_endpoint_authenticates_and_stops_only_after_response_closes(self):
        stop_callback = Mock()
        control = AuthenticatedLocalControl(
            lambda environ, start_response: [b"fallback"],
            instance_token="expected-token",
            stop_callback=stop_callback,
        )

        def request(token):
            captured = {}

            def start_response(status, headers):
                captured["status"] = status

            response = control(
                {
                    "PATH_INFO": "/__nacagencycrm__/stop",
                    "REQUEST_METHOD": "POST",
                    "HTTP_X_NACAGENCYCRM_INSTANCE_TOKEN": token,
                },
                start_response,
            )
            body = b"".join(response)
            return captured["status"], json.loads(body), response

        forbidden_status, _, forbidden_response = request("wrong-token")
        if hasattr(forbidden_response, "close"):
            forbidden_response.close()
        self.assertTrue(forbidden_status.startswith("403"))
        stop_callback.assert_not_called()

        ok_status, payload, ok_response = request("expected-token")
        self.assertTrue(ok_status.startswith("200"))
        self.assertEqual(payload["status"], "stopping")
        stop_callback.assert_not_called()
        ok_response.close()
        stop_callback.assert_called_once_with()

    def test_finalize_runtime_waits_for_scheduled_shutdown_before_releasing_singleton(self):
        events = []
        runtime_state = Mock()
        runtime_state.unlink.side_effect = lambda **_: events.append("state-removed")
        runtime_lock = Mock()
        runtime_lock.close.side_effect = lambda: events.append("lock-released")
        timer = Mock()
        timer.shutdown_errors = []
        timer.join.side_effect = lambda: events.append("shutdown-finished")

        _finalize_runtime_shutdown(
            runtime_state,
            runtime_lock,
            server=Mock(),
            listener=Mock(),
            shutdown_scheduled=True,
            shutdown_timer=timer,
        )

        self.assertEqual(
            events,
            ["shutdown-finished", "state-removed", "lock-released"],
        )

    def test_finalize_runtime_keeps_singleton_when_scheduled_shutdown_failed(self):
        runtime_state = Mock()
        runtime_lock = Mock()
        timer = Mock()
        timer.shutdown_errors = [RuntimeError("server close failed")]

        with self.assertRaisesRegex(RuntimeError, "server close failed"):
            _finalize_runtime_shutdown(
                runtime_state,
                runtime_lock,
                server=Mock(),
                listener=Mock(),
                shutdown_scheduled=True,
                shutdown_timer=timer,
            )

        timer.join.assert_called_once_with()
        runtime_state.unlink.assert_not_called()
        runtime_lock.close.assert_not_called()

    def test_maintenance_detection_checks_local_and_global_windows_mutexes(self):
        self.assertEqual(
            MAINTENANCE_MUTEX_NAMES,
            (
                "NacAgencyCRM-Installer-Maintenance-v1",
                r"Global\NacAgencyCRM-Installer-Maintenance-v1",
            ),
        )
        kernel32 = Mock()
        kernel32.OpenMutexW = Mock(side_effect=[0, 123])
        kernel32.CloseHandle = Mock()

        with (
            patch("windows_runtime.ctypes.WinDLL", return_value=kernel32),
            patch("windows_runtime.ctypes.set_last_error"),
            patch("windows_runtime.ctypes.get_last_error", return_value=2),
        ):
            self.assertTrue(_maintenance_is_active())

        self.assertEqual(
            [call.args[2] for call in kernel32.OpenMutexW.call_args_list],
            list(MAINTENANCE_MUTEX_NAMES),
        )
        kernel32.CloseHandle.assert_called_once_with(123)

    def test_maintenance_detection_treats_only_file_not_found_as_inactive(self):
        kernel32 = Mock()
        kernel32.OpenMutexW = Mock(side_effect=[0, 0])
        kernel32.CloseHandle = Mock()

        with (
            patch("windows_runtime.ctypes.WinDLL", return_value=kernel32),
            patch("windows_runtime.ctypes.set_last_error"),
            patch("windows_runtime.ctypes.get_last_error", side_effect=[2, 2]),
        ):
            self.assertFalse(_maintenance_is_active())

    def test_maintenance_detection_fails_closed_on_mutex_access_error(self):
        kernel32 = Mock()
        kernel32.OpenMutexW = Mock(return_value=0)
        kernel32.CloseHandle = Mock()

        with (
            patch("windows_runtime.ctypes.WinDLL", return_value=kernel32),
            patch("windows_runtime.ctypes.set_last_error"),
            patch("windows_runtime.ctypes.get_last_error", return_value=5),
            self.assertRaisesRegex(OSError, "inspeccionar.*mantenimiento"),
        ):
            _maintenance_is_active()

    def test_server_acquires_singleton_before_preparing_runtime_data(self):
        with tempfile.TemporaryDirectory() as directory:
            events = []
            runtime_lock = Mock()
            from windows_runtime import main

            with (
                patch("windows_runtime._maintenance_is_active", return_value=False),
                patch(
                    "windows_runtime.claim_server_instance",
                    side_effect=lambda *_args, **_kwargs: events.append("claim")
                    or runtime_lock,
                ),
                patch(
                    "windows_runtime._prepare_runtime",
                    side_effect=lambda *_args, **_kwargs: events.append("prepare")
                    or {"instance_token": "token"},
                ),
                patch("windows_runtime._configure_logging"),
                patch(
                    "windows_runtime._create_exclusive_listener",
                    side_effect=OSError("occupied"),
                ),
                self.assertRaisesRegex(RuntimeError, "ocupado"),
            ):
                main(["--no-browser", "--data-root", directory])

            self.assertEqual(events[:2], ["claim", "prepare"])

    def test_server_start_is_rejected_while_installer_maintenance_is_active(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("windows_runtime.resolve_runtime_paths") as resolve,
            patch("windows_runtime._prepare_runtime", return_value={"instance_token": "token"}),
            patch("windows_runtime._configure_logging"),
            patch("windows_runtime._maintenance_is_active", return_value=True, create=True),
            patch("windows_runtime.claim_server_instance") as claim,
        ):
            resolve.return_value = resolve_runtime_paths(
                data_root=Path(directory), bundle_root=Path(directory)
            )
            from windows_runtime import main

            with self.assertRaisesRegex(RuntimeError, "mantenimiento"):
                main(["--no-browser"])

        claim.assert_not_called()

    def test_postinstall_launch_waits_for_maintenance_mutex_release(self):
        with (
            patch("windows_runtime._maintenance_is_active", side_effect=[True, True, False]),
            patch("windows_runtime.time.monotonic", side_effect=[0, 0, 0, 1]),
            patch("windows_runtime.time.sleep") as sleep,
        ):
            _wait_for_maintenance_end(timeout=10)

        self.assertEqual(sleep.call_count, 2)

    def test_installer_maintenance_requires_explicit_root_and_whitelisted_command(self):
        from windows_runtime import main

        with tempfile.TemporaryDirectory() as directory:
            paths = resolve_runtime_paths(directory, Path(directory) / "bundle")
            with (
                patch("windows_runtime.resolve_runtime_paths", return_value=paths),
                patch("windows_runtime._configure_logging"),
                self.assertRaisesRegex(RuntimeError, "raíz de datos explícita"),
            ):
                main(["--backup", "--installer-maintenance"])

        with (
            tempfile.TemporaryDirectory() as directory,
            patch(
                "windows_runtime._prepare_runtime",
                side_effect=AssertionError("unauthorized command reached preparation"),
            ),
            self.assertRaisesRegex(RuntimeError, "comando interno autorizado"),
        ):
            main(
                [
                    "--create-admin",
                    "--data-root",
                    directory,
                    "--installer-maintenance",
                ]
            )

    def test_unmarked_stop_is_rejected_during_installer_maintenance(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("windows_runtime._maintenance_is_active", return_value=True),
            patch("windows_runtime._port_is_open") as port_open,
            patch("windows_runtime._configure_logging"),
        ):
            from windows_runtime import main

            with self.assertRaisesRegex(RuntimeError, "mantenimiento"):
                main(["--stop", "--data-root", directory])

        port_open.assert_not_called()

    def test_installer_marked_stop_is_allowed_during_maintenance(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("windows_runtime._maintenance_is_active", return_value=True),
            patch("windows_runtime._installer_maintenance_authorized", return_value=True),
            patch("windows_runtime._port_is_open", return_value=False),
        ):
            from windows_runtime import main

            result = main(
                [
                    "--stop",
                    "--data-root",
                    directory,
                    "--installer-maintenance",
                ]
            )

        self.assertEqual(result, 0)

    def test_installer_maintenance_flag_requires_per_attempt_capability(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("windows_runtime._maintenance_is_active", return_value=True),
            patch("windows_runtime._installer_maintenance_authorized", return_value=False),
            patch("windows_runtime._port_is_open") as port_open,
        ):
            from windows_runtime import main

            with self.assertRaisesRegex(RuntimeError, "capacidad"):
                main(
                    [
                        "--stop",
                        "--data-root",
                        directory,
                        "--installer-maintenance",
                    ]
                )

        port_open.assert_not_called()

    def test_non_stop_commands_are_rejected_during_installer_maintenance(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("windows_runtime._maintenance_is_active", return_value=True),
            patch("windows_runtime._prepare_runtime") as prepare,
        ):
            from windows_runtime import main

            with self.assertRaisesRegex(RuntimeError, "mantenimiento"):
                main(["--backup", "--data-root", directory])

        prepare.assert_not_called()

    def test_backup_cli_recovers_pending_restore_before_reading_data(self):
        with tempfile.TemporaryDirectory() as directory:
            events = []
            lock = Mock()
            lock.acquire.return_value = True
            from windows_runtime import main

            with (
                patch("windows_runtime._configure_logging"),
                patch("windows_runtime.InterprocessFileLock", return_value=lock),
                patch(
                    "windows_runtime.recover_pending_restore",
                    side_effect=lambda _paths: events.append("recover"),
                ),
                patch(
                    "windows_runtime.create_backup_bundle",
                    side_effect=lambda _paths: events.append("backup"),
                ),
            ):
                result = main(["--backup", "--data-root", directory])

            self.assertEqual(result, 0)
            self.assertEqual(events, ["recover", "backup"])

    def test_backup_cli_on_empty_root_does_not_create_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "backup-report.txt"
            from windows_runtime import main

            with patch("windows_runtime._configure_logging"):
                result = main(
                    [
                        "--backup",
                        "--data-root",
                        str(root),
                        "--backup-report-file",
                        str(report),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(report.read_text(encoding="utf-8"), "")
            self.assertFalse((root / "config" / "secrets.json").exists())

    def test_backup_cli_writes_bundle_path_to_report_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.commit()
            report = root / "backup-report.txt"
            from windows_runtime import main

            with patch("windows_runtime._configure_logging"):
                result = main(
                    [
                        "--backup",
                        "--data-root",
                        str(root),
                        "--backup-report-file",
                        str(report),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue(Path(report.read_text(encoding="utf-8").strip()).is_file())

    def test_verify_backup_cli_rejects_tampered_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            ensure_runtime_config(root)
            paths.data.mkdir(parents=True)
            with closing(sqlite3.connect(paths.database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)")
                connection.commit()
            backup = create_backup_bundle(paths)
            assert backup is not None
            with zipfile.ZipFile(backup) as archive:
                manifest = archive.read("manifest.json")
                config = archive.read("config/secrets.json")
            with zipfile.ZipFile(backup, "w") as archive:
                archive.writestr("manifest.json", manifest)
                archive.writestr("data/crm.sqlite3", b"tampered")
                archive.writestr("config/secrets.json", config)

            from windows_runtime import main

            with self.assertRaisesRegex(RuntimeError, "integridad"):
                main(
                    [
                        "--verify-backup",
                        str(backup),
                        "--data-root",
                        str(root),
                    ]
                )

    def test_validate_bundle_rejects_a_missing_static_frontend(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from windows_runtime import main

            with (
                patch("windows_runtime._configure_logging"),
                self.assertRaisesRegex(RuntimeError, "frontend exportado"),
            ):
                main(
                    [
                        "--validate-bundle",
                        "--data-root",
                        str(root / "data-root"),
                    ]
                )

    def test_server_close_is_scheduled_after_the_stop_response_finishes(self):
        server = Mock()
        timer = Mock()
        with patch("windows_runtime.threading.Timer", return_value=timer) as timer_class:
            _schedule_server_close(server)

        timer_class.assert_called_once()
        self.assertEqual(timer_class.call_args.args[0], 0.25)
        self.assertTrue(callable(timer_class.call_args.args[1]))
        self.assertNotIn("args", timer_class.call_args.kwargs)
        self.assertFalse(timer.daemon)
        timer.start.assert_called_once_with()

    def test_server_close_scheduler_captures_shutdown_failures(self):
        server = Mock()
        server.close.side_effect = RuntimeError("server close failed")
        timer = Mock()

        with patch("windows_runtime.threading.Timer", return_value=timer) as timer_class:
            scheduled = _schedule_server_close(server)
            shutdown_target = timer_class.call_args.args[1]
            shutdown_target(*timer_class.call_args.kwargs.get("args", ()))

        self.assertIs(scheduled.timer, timer)
        self.assertEqual(len(scheduled.shutdown_errors), 1)
        self.assertRegex(str(scheduled.shutdown_errors[0]), "server close failed")

    def test_waitress_shutdown_waits_until_every_worker_has_exited(self):
        server = Mock()
        first_channel = Mock()
        second_channel = Mock()
        server.active_channels = {1: first_channel, 2: second_channel}

        class Dispatcher:
            def __init__(self):
                self.threads = {1}
                self.calls = []

            def shutdown(self, cancel_pending, timeout):
                self.calls.append((cancel_pending, timeout))
                if len(self.calls) == 2:
                    self.threads.clear()

        dispatcher = Dispatcher()
        server.task_dispatcher = dispatcher

        _shutdown_waitress(server)

        server.close.assert_called_once_with()
        first_channel.close.assert_called_once_with()
        second_channel.close.assert_called_once_with()
        self.assertEqual(
            dispatcher.calls,
            [(True, 5), (False, 5)],
        )

    def test_probe_rejects_an_unrelated_listener_on_the_expected_port(self):
        response = Mock()
        response.status = 200
        response.read.return_value = json.dumps(
            {"application": "AnotherApplication", "status": "ok"}
        ).encode("utf-8")
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)

        with patch("windows_runtime.urlopen", return_value=response):
            self.assertFalse(probe_running_instance(8000, "expected-token"))

    def test_stop_cli_allows_cleanup_when_config_is_corrupt_and_no_process_is_running(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = resolve_runtime_paths(root, root / "bundle")
            paths.config.mkdir(parents=True)
            paths.secrets_file.write_text("{invalid", encoding="utf-8")
            from windows_runtime import main

            with (
                patch("windows_runtime._port_is_open", return_value=False),
                patch("windows_runtime._configure_logging"),
            ):
                result = main(["--stop", "--data-root", str(root)])

            self.assertEqual(result, 0)

    def test_stop_treats_a_closed_port_as_already_stopped(self):
        with (
            patch("windows_runtime._port_is_open", return_value=False),
            patch("windows_runtime._authenticated_control_request") as request,
        ):
            self.assertFalse(stop_running_instance(8000, "expected-token"))

        request.assert_not_called()

    def test_stop_waits_until_the_authenticated_instance_has_stopped(self):
        with (
            patch("windows_runtime._port_is_open", return_value=True),
            patch(
                "windows_runtime._authenticated_control_request",
                return_value={"application": APP_NAME, "status": "stopping"},
            ),
            patch("windows_runtime.probe_running_instance", side_effect=[True, False]),
            patch("windows_runtime.time.sleep"),
        ):
            self.assertTrue(
                stop_running_instance(8000, "expected-token", wait_timeout=1)
            )

    def test_stop_waits_for_the_recorded_server_process_to_exit(self):
        state_file = Path("runtime.json")
        with (
            patch("windows_runtime._port_is_open", return_value=True),
            patch(
                "windows_runtime._authenticated_control_request",
                return_value={"application": APP_NAME, "status": "stopping"},
            ),
            patch("windows_runtime._read_runtime_state", return_value={"pid": 4321}),
            patch("windows_runtime._wait_for_process_exit", return_value=True) as wait,
        ):
            self.assertTrue(
                stop_running_instance(
                    8000,
                    "expected-token",
                    runtime_state_file=state_file,
                    wait_timeout=7,
                )
            )

        wait.assert_called_once_with(4321, 7)

    def test_stop_rejects_an_unrelated_listener(self):
        with (
            patch("windows_runtime._port_is_open", return_value=True),
            patch("windows_runtime._authenticated_control_request", return_value=None),
        ):
            with self.assertRaisesRegex(RuntimeError, "instancia autenticada"):
                stop_running_instance(8000, "expected-token")

    def test_singleton_rechecks_maintenance_after_acquiring_runtime_lock(self):
        mutex = Mock()
        mutex.acquire.return_value = True

        with (
            patch("windows_runtime.InterprocessFileLock", return_value=mutex),
            patch("windows_runtime._maintenance_is_active", return_value=True),
            self.assertRaisesRegex(RuntimeError, "mantenimiento"),
        ):
            claim_server_instance(
                Path(r"C:\Users\Alice\AppData\Local\NacAgencyCRM"),
                8000,
                "expected-token",
            )

        mutex.close.assert_called_once_with()

    def test_singleton_rejects_a_port_that_is_not_the_authenticated_crm(self):
        mutex = Mock()
        mutex.acquire.return_value = False
        with (
            patch("windows_runtime.InterprocessFileLock", return_value=mutex),
            patch("windows_runtime.probe_running_instance", return_value=False),
        ):
            with self.assertRaisesRegex(RuntimeError, "no responde como NacAgencyCRM"):
                claim_server_instance(
                    Path(r"C:\Users\Alice\AppData\Local\NacAgencyCRM"),
                    8000,
                    "expected-token",
                    wait_timeout=0,
                )

    def test_singleton_reloads_runtime_port_while_another_instance_starts(self):
        mutex = Mock()
        mutex.acquire.side_effect = [False, False, False]
        observed_ports = []

        def probe(port, _token):
            observed_ports.append(port)
            return port == 8001

        with (
            patch("windows_runtime.InterprocessFileLock", return_value=mutex),
            patch(
                "windows_runtime._read_runtime_state",
                side_effect=[{}, {"port": 8001}],
            ),
            patch("windows_runtime.probe_running_instance", side_effect=probe),
            patch("windows_runtime.time.monotonic", side_effect=[0, 0, 2]),
            patch("windows_runtime.time.sleep"),
        ):
            result = claim_server_instance(
                Path(r"C:\Users\Alice\AppData\Local\NacAgencyCRM"),
                8000,
                "expected-token",
                wait_timeout=1,
            )

        self.assertIsNone(result)
        self.assertEqual(observed_ports, [8000, 8001])

    def test_singleton_reloads_instance_token_created_by_winning_startup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config" / "secrets.json"
            mutex = Mock()
            mutex.acquire.side_effect = [False, False, False]
            observed_tokens = []

            def probe(_port, token):
                observed_tokens.append(token)
                if len(observed_tokens) == 1:
                    config.parent.mkdir(parents=True, exist_ok=True)
                    config.write_text(
                        json.dumps(
                            {
                                "django_secret_key": "d" * 64,
                                "jwt_signing_key": "j" * 64,
                                "smtp_encryption_key": "c" * 44,
                                "instance_token": "new-instance-token",
                            }
                        ),
                        encoding="utf-8",
                    )
                    return False
                return token == "new-instance-token"

            with (
                patch("windows_runtime.InterprocessFileLock", return_value=mutex),
                patch("windows_runtime._read_runtime_state", return_value={"port": 8000}),
                patch("windows_runtime.probe_running_instance", side_effect=probe),
                patch("windows_runtime.time.monotonic", side_effect=[0, 0, 2]),
                patch("windows_runtime.time.sleep"),
            ):
                result = claim_server_instance(root, 8000, "", wait_timeout=1)

        self.assertIsNone(result)
        self.assertEqual(observed_tokens, ["", "new-instance-token"])

    def test_singleton_is_keyed_by_data_root_not_port(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = claim_server_instance(root, 8000, "expected-token")
            self.assertIsNotNone(first)
            assert first is not None
            try:
                with self.assertRaisesRegex(RuntimeError, "otra instancia"):
                    claim_server_instance(
                        root,
                        8001,
                        "expected-token",
                        wait_timeout=0,
                    )
            finally:
                first.close()

    @skipUnless(os.name == "nt", "Exclusive port ownership is Windows-specific")
    def test_exclusive_listener_prevents_a_second_reusable_bind(self):
        listener = _create_exclusive_listener(0)
        try:
            port = listener.getsockname()[1]
            competing = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                competing.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                with self.assertRaises(OSError):
                    competing.bind(("127.0.0.1", port))
            finally:
                competing.close()
        finally:
            listener.close()
