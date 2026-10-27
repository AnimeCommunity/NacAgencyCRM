from pathlib import Path

from django.test import SimpleTestCase


class WindowsInstallerContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        repo_root = Path(__file__).resolve().parents[2]
        cls.script = (repo_root / "deploy" / "installer" / "NacAgencyCRM.iss").read_text(
            encoding="utf-8"
        )
        cls.build_script = (
            repo_root / "deploy" / "windows" / "build-windows.ps1"
        ).read_text(encoding="utf-8")

    def test_installer_serializes_setup_and_uninstall_with_cross_session_mutexes(self):
        self.assertIn(
            '#define MaintenanceMutexName "NacAgencyCRM-Installer-Maintenance-v1"',
            self.script,
        )
        self.assertIn(
            '#define GlobalMaintenanceMutexName "Global\\NacAgencyCRM-Installer-Maintenance-v1"',
            self.script,
        )
        self.assertIn(
            "SetupMutex={#MaintenanceMutexName},{#GlobalMaintenanceMutexName}",
            self.script,
        )
        uninstall = self.script.index("function InitializeUninstall")
        self.assertIn("AcquireUninstallMaintenanceMutexes", self.script[uninstall:])
        self.assertIn("ERROR_ALREADY_EXISTS", self.script)
        self.assertIn("procedure ReleaseUninstallMaintenanceMutexes", self.script)
        deinitialize = self.script.index("procedure DeinitializeUninstall")
        self.assertIn(
            "ReleaseUninstallMaintenanceMutexes",
            self.script[deinitialize:],
        )

    def test_candidate_bundle_is_validated_before_installed_files_are_changed(self):
        prepare = self.script.index("function PrepareToInstall")
        prepare_end = self.script.index("procedure CurStepChanged", prepare)
        prepare_body = self.script[prepare:prepare_end]
        self.assertIn("ExtractTemporaryFiles", prepare_body)
        self.assertLess(
            prepare_body.index("--validate-bundle"),
            prepare_body.index("--stop --data-root"),
        )

    def test_canonical_data_is_prepared_before_inno_commits_install_metadata(self):
        prepare = self.script.index("function PrepareToInstall")
        prepare_end = self.script.index("procedure CurStepChanged", prepare)
        prepare_body = self.script[prepare:prepare_end]
        self.assertGreaterEqual(prepare_body.count("--validate-bundle"), 2)
        self.assertIn("CanonicalDataRoot", prepare_body)

        cur_step = self.script.index("procedure CurStepChanged")
        cur_step_end = self.script.index("function GetCustomSetupExitCode", cur_step)
        cur_step_body = self.script[cur_step:cur_step_end]
        self.assertNotIn("RunHiddenAndWait", cur_step_body)
        self.assertNotIn("RaiseException", cur_step_body)
        self.assertIn("InstallSucceeded := True", cur_step_body)

    def test_installer_uses_explicit_canonical_data_root_and_backup_report(self):
        self.assertIn("--data-root", self.script)
        self.assertIn("--backup-report-file", self.script)
        self.assertIn("DatabaseExistedBefore", self.script)
        self.assertIn("BackupFile = ''", self.script)
        self.assertIn("not FileExists(BackupFile)", self.script)
        self.assertGreaterEqual(self.script.count("--installer-maintenance"), 5)

    def test_installer_authenticates_internal_maintenance_commands(self):
        self.assertIn("NACAGENCYCRM_INSTALLER_CAPABILITY_TOKEN", self.script)
        self.assertIn("NACAGENCYCRM_INSTALLER_CAPABILITY_FILE", self.script)
        self.assertIn("InitializeInstallerCapability", self.script)
        self.assertIn("ClearInstallerCapability", self.script)

    def test_update_migrates_candidate_before_publishing_canonical_data(self):
        prepare = self.script.index("function PrepareToInstall")
        prepare_end = self.script.index("procedure CurStepChanged", prepare)
        prepare_body = self.script[prepare:prepare_end]
        backup = prepare_body.index("--backup --data-root")
        verify = prepare_body.index("--verify-backup", backup)
        restore_candidate = prepare_body.index("--restore-backup", verify)
        second_validate = prepare_body.index("--validate-bundle", restore_candidate)
        self.assertLess(backup, verify)
        self.assertLess(verify, restore_candidate)
        self.assertLess(restore_candidate, second_validate)
        self.assertIn("PrepareCandidateDataCopy", prepare_body)
        candidate_validate_end = prepare_body.index("CandidateBackupReportFile", second_validate)
        self.assertIn(
            "CandidateDataRoot",
            prepare_body[second_validate:candidate_validate_end],
        )
        publish = prepare_body.index("--restore-backup", second_validate)
        while "CandidateBackupFile" not in prepare_body[publish : publish + 180]:
            publish = prepare_body.index("--restore-backup", publish + 1)
        self.assertIn("CanonicalDataRoot", prepare_body[publish : publish + 300])

    def test_update_rollback_material_survives_setup_process_termination(self):
        self.assertIn("MaintenanceDirectory", self.script)
        self.assertIn("UpdateJournalFile", self.script)
        self.assertIn("RecoverInterruptedInstall", self.script)
        self.assertIn("CanonicalDataRoot", self.script)
        self.assertNotIn("PreviousAppDirectory := ExpandConstant('{tmp}", self.script)

    def test_postinstall_launch_waits_until_setup_releases_maintenance_mutex(self):
        run_section = self.script.index("[Run]")
        code_section = self.script.index("[Code]", run_section)
        run_body = self.script[run_section:code_section]
        self.assertIn("--wait-for-maintenance", run_body)

    def test_failed_update_rolls_back_files_without_mutating_canonical_data(self):
        self.assertIn("function RollbackFailedInstall(): Boolean", self.script)
        self.assertIn("procedure DeinitializeSetup", self.script)
        self.assertIn("function GetCustomSetupExitCode", self.script)
        self.assertIn("CustomSetupExitCode := 4", self.script)
        self.assertIn("PreviousAppDirectory", self.script)
        self.assertIn("CandidateDataRoot", self.script)
        self.assertIn("UpdateJournalFile", self.script)
        rollback = self.script.index("function RollbackFailedInstall")
        prepare = self.script.index("function PrepareToInstall", rollback)
        self.assertNotIn("crm.sqlite3", self.script[rollback:prepare])

    def test_preinstall_rollback_never_deletes_an_untouched_app_directory(self):
        rollback = self.script.index("function RollbackFailedInstall")
        prepare = self.script.index("function PrepareToInstall", rollback)
        rollback_body = self.script[rollback:prepare]
        self.assertIn("function RollbackFailedInstall(): Boolean", rollback_body)
        self.assertNotIn("CandidateExe", rollback_body)
        self.assertNotIn("--restore-backup", rollback_body)
        self.assertLess(
            rollback_body.index("if InstallStarted then"),
            rollback_body.index("DelTree(ExpandConstant('{app}')"),
        )
        self.assertIn("AppDirectoryExistedBefore", rollback_body)

    def test_installer_owned_stop_commands_are_marked_for_maintenance(self):
        stop_marker = "--stop --data-root"
        stop_offsets = []
        search_from = 0
        while True:
            stop = self.script.find(stop_marker, search_from)
            if stop < 0:
                break
            stop_offsets.append(stop)
            search_from = stop + len(stop_marker)
        self.assertGreaterEqual(len(stop_offsets), 2)
        for stop in stop_offsets:
            self.assertIn("--installer-maintenance", self.script[stop : stop + 250])

    def test_uninstall_requires_a_reported_backup_artifact_for_existing_data(self):
        uninstall = self.script.index("function InitializeUninstall")
        uninstall_body = self.script[uninstall:]
        self.assertIn("--backup-report-file", uninstall_body)
        self.assertIn("DatabaseExistedBeforeUninstall", uninstall_body)
        self.assertIn("LoadStringFromFile", uninstall_body)
        self.assertIn("FileExists(UninstallBackupFile)", uninstall_body)

    def test_prepare_snapshots_any_preexisting_target_and_resets_attempt_state(self):
        prepare = self.script.index("function PrepareToInstall")
        prepare_end = self.script.index("procedure CurStepChanged", prepare)
        prepare_body = self.script[prepare:prepare_end]
        self.assertIn("AppDirectoryExistedBefore := DirExists", prepare_body)
        self.assertIn("RollbackCompleted := False", prepare_body)
        self.assertIn("InstallStarted := False", prepare_body)
        self.assertIn("InstallSucceeded := False", prepare_body)
        self.assertIn("AttemptActive := False", prepare_body)

    def test_canonical_build_runs_all_release_quality_gates(self):
        self.assertIn("npm audit --audit-level=high", self.build_script)
        self.assertIn("npx tsc --noEmit", self.build_script)
        self.assertIn("manage.py makemigrations --check --dry-run", self.build_script)
        self.assertIn("manage.py check", self.build_script)
        self.assertIn("-m pip check", self.build_script)
