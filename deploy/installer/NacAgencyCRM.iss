#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppName "NacAgencyCRM"
#define MyAppPublisher "NAC Agency"
#define MyAppExeName "NacAgencyCRM.exe"
#define MaintenanceMutexName "NacAgencyCRM-Installer-Maintenance-v1"
#define GlobalMaintenanceMutexName "Global\NacAgencyCRM-Installer-Maintenance-v1"

[Setup]
AppId={{2E251F4F-276B-4F57-A2C6-E0BFE139AE5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
OutputDir=Output
OutputBaseFilename=NacAgencyCRM-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes
CloseApplications=no
RestartApplications=no
SetupMutex={#MaintenanceMutexName},{#GlobalMaintenanceMutexName}

[Files]
Source: "..\..\dist\windows\NacAgencyCRM\*"; DestDir: "candidate"; Flags: dontcopy noencryption recursesubdirs createallsubdirs
Source: "..\..\dist\windows\NacAgencyCRM\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\windows\start-hidden.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\windows\stop-hidden.vbs"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\{#MyAppExeName}"

[Icons]
Name: "{userprograms}\{#MyAppName}\Abrir CRM"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\start-hidden.vbs"""; WorkingDir: "{app}"
Name: "{userprograms}\{#MyAppName}\Crear administrador"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--create-admin"; WorkingDir: "{app}"
Name: "{userprograms}\{#MyAppName}\Respaldar datos"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--backup"; WorkingDir: "{app}"
Name: "{userprograms}\{#MyAppName}\Detener CRM"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\stop-hidden.vbs"""; WorkingDir: "{app}"
Name: "{userprograms}\{#MyAppName}\Abrir carpeta de datos"; Filename: "{sys}\explorer.exe"; Parameters: """{localappdata}\NacAgencyCRM"""
Name: "{userdesktop}\NacAgencyCRM"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\start-hidden.vbs"""; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce
Name: "autostart"; Description: "Iniciar NacAgencyCRM al iniciar sesión"; GroupDescription: "Inicio automático:"; Flags: unchecked

[Icons]
Name: "{userstartup}\NacAgencyCRM"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\start-hidden.vbs"""; WorkingDir: "{app}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--wait-for-maintenance"; WorkingDir: "{app}"; Description: "Abrir NacAgencyCRM"; Flags: postinstall skipifsilent nowait runhidden

[Code]
var
  CandidateDirectory: String;
  CandidateExe: String;
  CandidateDataRoot: String;
  CanonicalDataRoot: String;
  MaintenanceDirectory: String;
  PreviousAppDirectory: String;
  PreviousSecretsFile: String;
  RollbackBackupFile: String;
  UpdateJournalFile: String;
  BackupReportFile: String;
  BackupFile: String;
  CandidateBackupReportFile: String;
  CandidateBackupFile: String;
  InstallerCapabilityToken: String;
  InstallerCapabilityFile: String;
  ExistingInstall: Boolean;
  AppDirectoryExistedBefore: Boolean;
  DatabaseExistedBefore: Boolean;
  SecretsExistedBefore: Boolean;
  InstanceWasRunning: Boolean;
  RestartAfterSetup: Boolean;
  InstallStarted: Boolean;
  DataPrepared: Boolean;
  InstallSucceeded: Boolean;
  AttemptActive: Boolean;
  RollbackCompleted: Boolean;
  CustomSetupExitCode: Integer;
  UninstallMaintenanceMutex: THandle;
  GlobalUninstallMaintenanceMutex: THandle;

const
  ERROR_ALREADY_EXISTS = 183;

function CreateMutexW(
  MutexAttributes: Integer;
  InitialOwner: Boolean;
  Name: String
): THandle;
  external 'CreateMutexW@kernel32.dll stdcall';
function CloseHandle(Handle: THandle): Boolean;
  external 'CloseHandle@kernel32.dll stdcall';
function GetLastError(): LongWord;
  external 'GetLastError@kernel32.dll stdcall';
function SetEnvironmentVariableW(Name, Value: String): Boolean;
  external 'SetEnvironmentVariableW@kernel32.dll stdcall';

function TryCreateMaintenanceMutex(const Name: String; var Handle: THandle): Boolean;
begin
  Handle := CreateMutexW(0, False, Name);
  Result := Handle <> 0;
  if Result and (GetLastError() = ERROR_ALREADY_EXISTS) then
  begin
    CloseHandle(Handle);
    Handle := 0;
    Result := False;
  end;
end;

function AcquireUninstallMaintenanceMutexes(): Boolean;
begin
  Result := TryCreateMaintenanceMutex(
    '{#MaintenanceMutexName}',
    UninstallMaintenanceMutex
  );
  if not Result then
    Exit;

  Result := TryCreateMaintenanceMutex(
    '{#GlobalMaintenanceMutexName}',
    GlobalUninstallMaintenanceMutex
  );
  if not Result then
  begin
    CloseHandle(UninstallMaintenanceMutex);
    UninstallMaintenanceMutex := 0;
  end;
end;

procedure ReleaseUninstallMaintenanceMutexes();
begin
  if GlobalUninstallMaintenanceMutex <> 0 then
  begin
    CloseHandle(GlobalUninstallMaintenanceMutex);
    GlobalUninstallMaintenanceMutex := 0;
  end;
  if UninstallMaintenanceMutex <> 0 then
  begin
    CloseHandle(UninstallMaintenanceMutex);
    UninstallMaintenanceMutex := 0;
  end;
end;

procedure ClearInstallerCapability();
begin
  SetEnvironmentVariableW('NACAGENCYCRM_INSTALLER_CAPABILITY_TOKEN', '');
  SetEnvironmentVariableW('NACAGENCYCRM_INSTALLER_CAPABILITY_FILE', '');
  if InstallerCapabilityFile <> '' then
    DeleteFile(InstallerCapabilityFile);
  InstallerCapabilityToken := '';
  InstallerCapabilityFile := '';
end;

function InitializeInstallerCapability(): Boolean;
var
  RawToken: AnsiString;
begin
  if (InstallerCapabilityToken <> '') and FileExists(InstallerCapabilityFile) then
  begin
    Result := True;
    Exit;
  end;

  ClearInstallerCapability();
  RawToken := GetDateTimeString('yyyymmddhhnnss', '-', ':') + '|' +
    IntToStr(Random(1000000000)) + '|' +
    IntToStr(Random(1000000000)) + '|' +
    IntToStr(Random(1000000000)) + '|' +
    IntToStr(Random(1000000000)) + '|' +
    ExpandConstant('{tmp}') + '|' + ExpandConstant('{app}');
  InstallerCapabilityToken := GetSHA256OfString(RawToken);
  InstallerCapabilityFile := AddBackslash(ExpandConstant('{tmp}')) +
    'nacagencycrm-installer-' + InstallerCapabilityToken + '.cap';

  Result := SaveStringToFile(
    InstallerCapabilityFile,
    InstallerCapabilityToken,
    False
  ) and SetEnvironmentVariableW(
    'NACAGENCYCRM_INSTALLER_CAPABILITY_TOKEN',
    InstallerCapabilityToken
  ) and SetEnvironmentVariableW(
    'NACAGENCYCRM_INSTALLER_CAPABILITY_FILE',
    InstallerCapabilityFile
  );
  if not Result then
    ClearInstallerCapability();
end;

function CopyDirectoryTree(const SourceDirectory, DestinationDirectory: String): Boolean;
var
  FindRec: TFindRec;
  SourcePath: String;
  DestinationPath: String;
begin
  Result := ForceDirectories(DestinationDirectory);
  if not Result then
    Exit;

  if FindFirst(AddBackslash(SourceDirectory) + '*', FindRec) then
  begin
    try
      repeat
        if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
        begin
          SourcePath := AddBackslash(SourceDirectory) + FindRec.Name;
          DestinationPath := AddBackslash(DestinationDirectory) + FindRec.Name;
          if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0 then
          begin
            if not CopyDirectoryTree(SourcePath, DestinationPath) then
            begin
              Result := False;
              Exit;
            end;
          end
          else if not CopyFile(SourcePath, DestinationPath, False) then
          begin
            Result := False;
            Exit;
          end;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

function RunHiddenAndWait(
  const Executable, Parameters, WorkingDirectory: String;
  var ResultCode: Integer
): Boolean;
begin
  Result := Exec(
    Executable,
    Parameters,
    WorkingDirectory,
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
end;

function PrepareCandidateDataCopy(): Boolean;
begin
  DelTree(CandidateDataRoot, True, True, True);
  Result := ForceDirectories(AddBackslash(CandidateDataRoot) + 'data') and
    ForceDirectories(AddBackslash(CandidateDataRoot) + 'config');
  if not Result then
    Exit;
  if DatabaseExistedBefore then
    Result := CopyFile(
      AddBackslash(CanonicalDataRoot) + 'data\crm.sqlite3',
      AddBackslash(CandidateDataRoot) + 'data\crm.sqlite3',
      False
    );
  if Result and SecretsExistedBefore then
    Result := CopyFile(
      AddBackslash(CanonicalDataRoot) + 'config\secrets.json',
      AddBackslash(CandidateDataRoot) + 'config\secrets.json',
      False
    );
end;

procedure CleanupUpdateJournal();
begin
  if UpdateJournalFile <> '' then
    DeleteFile(UpdateJournalFile);
  if MaintenanceDirectory <> '' then
    DelTree(MaintenanceDirectory, True, True, True);
end;

function CreateUpdateJournal(): Boolean;
var
  JournalState: String;
begin
  DelTree(MaintenanceDirectory, True, True, True);
  Result := ForceDirectories(MaintenanceDirectory);
  if not Result then
    Exit;

  JournalState := 'prepared:';
  if AppDirectoryExistedBefore then
  begin
    Result := CopyDirectoryTree(ExpandConstant('{app}'), PreviousAppDirectory);
    JournalState := JournalState + '1';
  end
  else
    JournalState := JournalState + '0';

  if DatabaseExistedBefore then
  begin
    JournalState := JournalState + '1';
    if Result then
      Result := (BackupFile <> '') and FileExists(BackupFile) and
        CopyFile(BackupFile, RollbackBackupFile, False);
  end
  else
    JournalState := JournalState + '0';

  if SecretsExistedBefore then
  begin
    JournalState := JournalState + '1';
    if Result and (not DatabaseExistedBefore) then
      Result := CopyFile(
        AddBackslash(CanonicalDataRoot) + 'config\secrets.json',
        PreviousSecretsFile,
        False
      );
  end
  else
    JournalState := JournalState + '0';

  if Result then
    Result := SaveStringToFile(UpdateJournalFile, JournalState, False);
  if not Result then
    CleanupUpdateJournal();
end;

function RestoreCanonicalDataState(): Boolean;
var
  ResultCode: Integer;
  DatabaseFile: String;
  SecretsFile: String;
begin
  DatabaseFile := AddBackslash(CanonicalDataRoot) + 'data\crm.sqlite3';
  SecretsFile := AddBackslash(CanonicalDataRoot) + 'config\secrets.json';
  if DatabaseExistedBefore then
  begin
    if not FileExists(RollbackBackupFile) then
    begin
      Result := False;
      Exit;
    end;
    Result := RunHiddenAndWait(
      CandidateExe,
      '--restore-backup ' + AddQuotes(RollbackBackupFile) +
        ' --data-root ' + AddQuotes(CanonicalDataRoot) +
        ' --installer-maintenance',
      CandidateDirectory,
      ResultCode
    ) and (ResultCode = 0);
    Exit;
  end;

  Result := True;
  if FileExists(DatabaseFile) then
    Result := DeleteFile(DatabaseFile);
  if Result and SecretsExistedBefore then
    Result := FileExists(PreviousSecretsFile) and
      ForceDirectories(ExtractFileDir(SecretsFile)) and
      CopyFile(PreviousSecretsFile, SecretsFile, False)
  else if Result and FileExists(SecretsFile) then
    Result := DeleteFile(SecretsFile);
end;

function RecoverInterruptedInstall(): Boolean;
var
  JournalState: AnsiString;
  PreviousAppExisted: Boolean;
begin
  if not FileExists(UpdateJournalFile) then
  begin
    Result := True;
    Exit;
  end;
  if not LoadStringFromFile(UpdateJournalFile, JournalState) then
  begin
    Result := False;
    Exit;
  end;
  JournalState := Trim(JournalState);
  if JournalState = 'committed' then
  begin
    CleanupUpdateJournal();
    Result := True;
    Exit;
  end;
  if (Length(JournalState) <> 12) or
    (Copy(JournalState, 1, 9) <> 'prepared:') then
  begin
    Result := False;
    Exit;
  end;
  PreviousAppExisted := Copy(JournalState, 10, 1) = '1';
  AppDirectoryExistedBefore := PreviousAppExisted;
  DatabaseExistedBefore := Copy(JournalState, 11, 1) = '1';
  SecretsExistedBefore := Copy(JournalState, 12, 1) = '1';
  if PreviousAppExisted and
    (not FileExists(AddBackslash(PreviousAppDirectory) + '{#MyAppExeName}')) then
  begin
    Result := False;
    Exit;
  end;
  if DatabaseExistedBefore and (not FileExists(RollbackBackupFile)) then
  begin
    Result := False;
    Exit;
  end;
  if (not DatabaseExistedBefore) and SecretsExistedBefore and
    (not FileExists(PreviousSecretsFile)) then
  begin
    Result := False;
    Exit;
  end;
  Result := RestoreCanonicalDataState();
  if Result then
    Result := DelTree(ExpandConstant('{app}'), True, True, True);
  if Result and PreviousAppExisted then
    Result := DirExists(PreviousAppDirectory) and
      CopyDirectoryTree(PreviousAppDirectory, ExpandConstant('{app}'));
  if Result then
    CleanupUpdateJournal();
end;

function MarkUpdateCommitted(): Boolean;
begin
  Result := SaveStringToFile(UpdateJournalFile, 'committed', False);
end;

procedure LaunchAfterMaintenance(const Executable: String; NoBrowser: Boolean);
var
  ResultCode: Integer;
  Parameters: String;
begin
  if not FileExists(Executable) then
    Exit;
  Parameters := '--wait-for-maintenance';
  if NoBrowser then
    Parameters := Parameters + ' --no-browser';
  if not Exec(
    Executable,
    Parameters,
    ExtractFileDir(Executable),
    SW_HIDE,
    ewNoWait,
    ResultCode
  ) then
    Log('ERROR: The restored NacAgencyCRM instance could not be scheduled to restart.');
end;

function RollbackFailedInstall(): Boolean;
var
  AppRestored: Boolean;
  DataRestored: Boolean;
begin
  if RollbackCompleted then
  begin
    Result := True;
    Exit;
  end;

  Log('Rolling back failed NacAgencyCRM installation or update.');
  DataRestored := RestoreCanonicalDataState();
  AppRestored := True;
  if InstallStarted then
  begin
    AppRestored := DelTree(ExpandConstant('{app}'), True, True, True);
    if AppRestored and AppDirectoryExistedBefore then
      AppRestored := DirExists(PreviousAppDirectory) and
        CopyDirectoryTree(PreviousAppDirectory, ExpandConstant('{app}'));
  end;

  Result := AppRestored and DataRestored;
  if Result then
  begin
    CleanupUpdateJournal();
    RollbackCompleted := True;
    AttemptActive := False;
    RestartAfterSetup := InstanceWasRunning;
    Log('The failed installation or update was rolled back.');
  end
  else
    Log('ERROR: The failed installation or update could not be rolled back completely.');
end;

function AbortAttempt(const MessageText: String): String;
begin
  CustomSetupExitCode := 4;
  if RollbackFailedInstall() then
    Result := MessageText
  else
    Result := MessageText +
      ' La reversión no pudo completarse; conserve los respaldos y revise el registro del instalador.';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  ExistingExe: String;
  BackupReport: AnsiString;
  CandidateBackupReport: AnsiString;
  PreviousAttemptWasActive: Boolean;
begin
  Result := '';
  PreviousAttemptWasActive := AttemptActive;
  if AttemptActive and (not RollbackFailedInstall()) then
  begin
    Result := 'No fue posible completar la reversión del intento anterior. La instalación no puede continuar.';
    Exit;
  end;
  InstallStarted := False;
  DataPrepared := False;
  InstallSucceeded := False;
  AttemptActive := False;
  RollbackCompleted := False;
  if not PreviousAttemptWasActive then
  begin
    ExistingInstall := False;
    AppDirectoryExistedBefore := False;
    DatabaseExistedBefore := False;
    SecretsExistedBefore := False;
    InstanceWasRunning := False;
    RestartAfterSetup := False;
  end;
  CustomSetupExitCode := 0;
  CanonicalDataRoot := ExpandConstant('{localappdata}\NacAgencyCRM');
  MaintenanceDirectory := AddBackslash(CanonicalDataRoot) +
    'maintenance\installer-update-v1';
  PreviousAppDirectory := AddBackslash(MaintenanceDirectory) + 'previous-app';
  PreviousSecretsFile := AddBackslash(MaintenanceDirectory) + 'previous-secrets.json';
  RollbackBackupFile := AddBackslash(MaintenanceDirectory) + 'rollback.zip';
  UpdateJournalFile := AddBackslash(MaintenanceDirectory) + 'active.txt';
  CandidateDirectory := ExpandConstant('{tmp}\candidate');
  CandidateExe := AddBackslash(CandidateDirectory) + '{#MyAppExeName}';
  CandidateDataRoot := ExpandConstant('{tmp}\candidate-data');
  BackupReportFile := ExpandConstant('{tmp}\backup-report.txt');
  BackupFile := '';
  CandidateBackupReportFile := ExpandConstant('{tmp}\candidate-backup-report.txt');
  CandidateBackupFile := '';
  ExistingExe := ExpandConstant('{app}\{#MyAppExeName}');

  if not InitializeInstallerCapability() then
  begin
    Result := 'No fue posible crear la capacidad privada de mantenimiento del instalador.';
    Exit;
  end;

  ExtractTemporaryFiles('candidate\*');
  if not FileExists(CandidateExe) then
  begin
    Result := 'El instalador no pudo extraer el paquete candidato para validarlo.';
    Exit;
  end;

  DelTree(CandidateDataRoot, True, True, True);
  if not RunHiddenAndWait(
    CandidateExe,
    '--validate-bundle --data-root ' + AddQuotes(CandidateDataRoot) +
      ' --installer-maintenance',
    CandidateDirectory,
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    Result := 'El paquete candidato no superó la validación previa. No se modificó la instalación existente.';
    Exit;
  end;

  if FileExists(UpdateJournalFile) then
  begin
    if not RunHiddenAndWait(
      CandidateExe,
      '--stop --data-root ' + AddQuotes(CanonicalDataRoot) +
        ' --installer-maintenance',
      CandidateDirectory,
      ResultCode
    ) or (ResultCode <> 0) or (not RecoverInterruptedInstall()) then
    begin
      Result := 'No fue posible recuperar una actualización interrumpida anteriormente.';
      Exit;
    end;
  end;

  ExistingInstall := FileExists(ExistingExe);
  AppDirectoryExistedBefore := DirExists(ExpandConstant('{app}'));
  DatabaseExistedBefore := FileExists(AddBackslash(CanonicalDataRoot) + 'data\crm.sqlite3');
  SecretsExistedBefore := FileExists(AddBackslash(CanonicalDataRoot) + 'config\secrets.json');
  if FileExists(AddBackslash(CanonicalDataRoot) + 'config\runtime.json') then
    InstanceWasRunning := True;

  if ExistingInstall then
  begin
    if not RunHiddenAndWait(
      ExistingExe,
      '--stop --data-root ' + AddQuotes(CanonicalDataRoot) +
        ' --installer-maintenance',
      ExpandConstant('{app}'),
      ResultCode
    ) or (ResultCode <> 0) then
    begin
      Result := 'No fue posible detener la versión instalada. La actualización fue cancelada antes de reemplazar archivos.';
      Exit;
    end;
    RestartAfterSetup := InstanceWasRunning;
  end;

  DeleteFile(BackupReportFile);
  if not RunHiddenAndWait(
    CandidateExe,
    '--backup --data-root ' + AddQuotes(CanonicalDataRoot) +
      ' --backup-report-file ' + AddQuotes(BackupReportFile) +
      ' --installer-maintenance',
    CandidateDirectory,
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    CustomSetupExitCode := 4;
    Result := 'No fue posible crear el respaldo previo. La instalación fue cancelada antes de reemplazar archivos.';
    Exit;
  end;

  if FileExists(BackupReportFile) and LoadStringFromFile(BackupReportFile, BackupReport) then
    BackupFile := Trim(BackupReport);

  if ((BackupFile <> '') and (not FileExists(BackupFile))) or
    (DatabaseExistedBefore and ((BackupFile = '') or (not FileExists(BackupFile)))) then
  begin
    CustomSetupExitCode := 4;
    Result := 'El respaldo previo no produjo un archivo verificable. La instalación fue cancelada antes de reemplazar archivos.';
    Exit;
  end;

  if (BackupFile <> '') and (not RunHiddenAndWait(
    CandidateExe,
    '--verify-backup ' + AddQuotes(BackupFile) +
      ' --data-root ' + AddQuotes(CanonicalDataRoot) +
      ' --installer-maintenance',
    CandidateDirectory,
    ResultCode
  ) or (ResultCode <> 0)) then
  begin
    CustomSetupExitCode := 4;
    Result := 'El respaldo previo no superó la verificación de integridad. La instalación fue cancelada.';
    Exit;
  end;

  DelTree(CandidateDataRoot, True, True, True);
  if BackupFile <> '' then
  begin
    if not RunHiddenAndWait(
      CandidateExe,
      '--restore-backup ' + AddQuotes(BackupFile) +
        ' --data-root ' + AddQuotes(CandidateDataRoot) +
        ' --installer-maintenance',
      CandidateDirectory,
      ResultCode
    ) or (ResultCode <> 0) then
    begin
      CustomSetupExitCode := 4;
      Result := 'No fue posible restaurar el respaldo verificado en la copia aislada de validación.';
      Exit;
    end;
  end
  else if not PrepareCandidateDataCopy() then
  begin
    CustomSetupExitCode := 4;
    Result := 'No fue posible preparar una copia aislada de los datos para validar la actualización.';
    Exit;
  end;

  if not RunHiddenAndWait(
    CandidateExe,
    '--validate-bundle --data-root ' + AddQuotes(CandidateDataRoot) +
      ' --installer-maintenance',
    CandidateDirectory,
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    CustomSetupExitCode := 4;
    Result := 'La copia aislada de los datos no superó la migración de validación. La instalación fue cancelada.';
    Exit;
  end;

  DeleteFile(CandidateBackupReportFile);
  if not RunHiddenAndWait(
    CandidateExe,
    '--backup --data-root ' + AddQuotes(CandidateDataRoot) +
      ' --backup-report-file ' + AddQuotes(CandidateBackupReportFile) +
      ' --installer-maintenance',
    CandidateDirectory,
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    CustomSetupExitCode := 4;
    Result := 'No fue posible empaquetar la copia migrada de los datos.';
    Exit;
  end;
  if FileExists(CandidateBackupReportFile) and
    LoadStringFromFile(CandidateBackupReportFile, CandidateBackupReport) then
    CandidateBackupFile := Trim(CandidateBackupReport);
  if (CandidateBackupFile = '') or (not FileExists(CandidateBackupFile)) then
  begin
    CustomSetupExitCode := 4;
    Result := 'La copia migrada no produjo un respaldo publicable.';
    Exit;
  end;
  if not RunHiddenAndWait(
    CandidateExe,
    '--verify-backup ' + AddQuotes(CandidateBackupFile) +
      ' --data-root ' + AddQuotes(CandidateDataRoot) +
      ' --installer-maintenance',
    CandidateDirectory,
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    CustomSetupExitCode := 4;
    Result := 'La copia migrada no superó la verificación final.';
    Exit;
  end;

  if not CreateUpdateJournal() then
  begin
    CustomSetupExitCode := 4;
    Result := 'No fue posible conservar una copia persistente de la instalación anterior.';
    Exit;
  end;
  AttemptActive := True;

  if not RunHiddenAndWait(
    CandidateExe,
    '--restore-backup ' + AddQuotes(CandidateBackupFile) +
      ' --data-root ' + AddQuotes(CanonicalDataRoot) +
      ' --installer-maintenance',
    CandidateDirectory,
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    Result := AbortAttempt(
      'No fue posible publicar de forma segura los datos preparados para la nueva versión.'
    );
    Exit;
  end;
  DataPrepared := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    InstallStarted := True;

  if CurStep = ssDone then
  begin
    if MarkUpdateCommitted() then
      CleanupUpdateJournal()
    else
      Log('ERROR: The completed update journal could not be marked as committed.');
    InstallSucceeded := True;
    AttemptActive := False;
  end;
end;

function GetCustomSetupExitCode(): Integer;
begin
  Result := CustomSetupExitCode;
end;

procedure DeinitializeSetup;
begin
  if AttemptActive and not InstallSucceeded then
  begin
    CustomSetupExitCode := 4;
    if not RollbackFailedInstall() then
      Log('ERROR: Setup ended before the rollback could complete.');
  end;
  if RestartAfterSetup then
    LaunchAfterMaintenance(
      ExpandConstant('{app}\{#MyAppExeName}'),
      True
    );
  ClearInstallerCapability();
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
  DataRoot: String;
  UninstallBackupReportFile: String;
  UninstallBackupFile: String;
  UninstallBackupReport: AnsiString;
  DatabaseExistedBeforeUninstall: Boolean;
begin
  Result := False;
  DataRoot := ExpandConstant('{localappdata}\NacAgencyCRM');
  UninstallBackupReportFile := ExpandConstant('{tmp}\uninstall-backup-report.txt');
  UninstallBackupFile := '';
  DatabaseExistedBeforeUninstall := FileExists(
    AddBackslash(DataRoot) + 'data\crm.sqlite3'
  );

  if not AcquireUninstallMaintenanceMutexes() then
  begin
    MsgBox(
      'Ya hay otra instalación, actualización o desinstalación de NacAgencyCRM en curso.',
      mbError,
      MB_OK
    );
    Exit;
  end;

  if not InitializeInstallerCapability() then
  begin
    MsgBox(
      'No fue posible crear la capacidad privada de mantenimiento del desinstalador.',
      mbError,
      MB_OK
    );
    ReleaseUninstallMaintenanceMutexes();
    Exit;
  end;

  if (not UninstallSilent) and (MsgBox(
    'La aplicación será desinstalada. Los datos y respaldos se conservarán en:' + #13#10 +
    DataRoot + #13#10#13#10 +
    '¿Desea continuar?',
    mbConfirmation,
    MB_YESNO
  ) <> IDYES) then
    Exit;

  if not RunHiddenAndWait(
    ExpandConstant('{app}\{#MyAppExeName}'),
    '--stop --data-root ' + AddQuotes(DataRoot) +
      ' --installer-maintenance',
    ExpandConstant('{app}'),
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    MsgBox(
      'No fue posible detener NacAgencyCRM de forma segura. La desinstalación fue cancelada.',
      mbError,
      MB_OK
    );
    Exit;
  end;

  DeleteFile(UninstallBackupReportFile);
  if not RunHiddenAndWait(
    ExpandConstant('{app}\{#MyAppExeName}'),
    '--backup --data-root ' + AddQuotes(DataRoot) +
      ' --backup-report-file ' + AddQuotes(UninstallBackupReportFile) +
      ' --installer-maintenance',
    ExpandConstant('{app}'),
    ResultCode
  ) or (ResultCode <> 0) then
  begin
    MsgBox(
      'No fue posible crear el respaldo previo. La desinstalación fue cancelada y los datos permanecen intactos.',
      mbError,
      MB_OK
    );
    Exit;
  end;

  if FileExists(UninstallBackupReportFile) and
    LoadStringFromFile(UninstallBackupReportFile, UninstallBackupReport) then
    UninstallBackupFile := Trim(UninstallBackupReport);

  if DatabaseExistedBeforeUninstall and
    ((UninstallBackupFile = '') or (not FileExists(UninstallBackupFile))) then
  begin
    MsgBox(
      'El respaldo previo no produjo un archivo verificable. La desinstalación fue cancelada.',
      mbError,
      MB_OK
    );
    Exit;
  end;

  if (UninstallBackupFile <> '') and (not RunHiddenAndWait(
    ExpandConstant('{app}\{#MyAppExeName}'),
    '--verify-backup ' + AddQuotes(UninstallBackupFile) +
      ' --data-root ' + AddQuotes(DataRoot) +
      ' --installer-maintenance',
    ExpandConstant('{app}'),
    ResultCode
  ) or (ResultCode <> 0)) then
  begin
    MsgBox(
      'El respaldo previo no superó la verificación de integridad. La desinstalación fue cancelada.',
      mbError,
      MB_OK
    );
    Exit;
  end;

  Result := True;
end;

procedure DeinitializeUninstall();
begin
  ClearInstallerCapability();
  ReleaseUninstallMaintenanceMutexes();
end;
