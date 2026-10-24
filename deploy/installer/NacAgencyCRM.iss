#define AppName "NacAgencyCRM"
#define AppVersion "1.0.0"
#define AppPublisher "ANC Agency"

[Setup]
AppId=NacAgencyCRM.Local
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}

DefaultDirName={localappdata}\NacAgencyCRM
DefaultGroupName=NacAgencyCRM

OutputDir=Output
OutputBaseFilename=NacAgencyCRM-Setup-{#AppVersion}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
UninstallDisplayName=NacAgencyCRM
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\compose.client.yml"; \
    DestDir: "{app}"; \
    Flags: ignoreversion

Source: "..\images\*"; \
    DestDir: "{app}\images"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

Source: "..\scripts\*"; \
    DestDir: "{app}\scripts"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

Source: "..\assets\*"; \
    DestDir: "{app}\assets"; \
    Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\Abrir NacAgencyCRM"; \
    Filename: "{app}\scripts\iniciar-crm.bat"; \
    WorkingDir: "{app}"

Name: "{group}\Detener NacAgencyCRM"; \
    Filename: "{app}\scripts\detener-crm.bat"; \
    WorkingDir: "{app}"

Name: "{group}\Crear administrador"; \
    Filename: "{app}\scripts\crear-administrador.bat"; \
    WorkingDir: "{app}"

Name: "{group}\Respaldar NacAgencyCRM"; \
    Filename: "{app}\scripts\respaldar-crm.bat"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\NacAgencyCRM"; \
    Filename: "{app}\scripts\iniciar-crm.bat"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

[Tasks]
Name: "desktopicon"; \
    Description: "Crear acceso directo en el escritorio"; \
    GroupDescription: "Accesos directos:"; \
    Flags: checkedonce

[Run]
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\preparar-instalacion.ps1"""; \
    WorkingDir: "{app}"; \
    StatusMsg: "Preparando NacAgencyCRM..."; \
    Flags: waituntilterminated

Filename: "{app}\scripts\iniciar-crm.bat"; \
    Description: "Abrir NacAgencyCRM"; \
    WorkingDir: "{app}"; \
    Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\scripts\detener-crm.bat"; \
    RunOnceId: "StopNacAgencyCRM"; \
    Flags: runhidden

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result :=
    Exec(
      ExpandConstant('{cmd}'),
      '/C docker --version >NUL 2>&1',
      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode
    )
    and (ResultCode = 0);

  if not Result then
  begin
    MsgBox(
      'Docker Desktop no está instalado.' + #13#10 + #13#10 +
      'Instala y abre Docker Desktop antes de instalar NacAgencyCRM.',
      mbError,
      MB_OK
    );
  end;
end;