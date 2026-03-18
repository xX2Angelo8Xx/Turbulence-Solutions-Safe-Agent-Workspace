; Inno Setup Script for Agent Environment Launcher
; Generated for INS-005 — wraps PyInstaller --onedir output

#define MyAppName "Agent Environment Launcher"
#define MyAppVersion "2.1.3"
#define MyAppPublisher "Turbulence Solutions"
#define MyAppExeName "launcher.exe"

[Setup]
AppId={{B8F4E5A2-7C3D-4E6F-9A1B-2D5E8F0C3A7D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=AgentEnvironmentLauncher-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\..\dist\launcher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
; Silent installs (in-app update via /SILENT) skip the postinstall entry above.
; This second entry unconditionally relaunches the app after a silent install.
Filename: "{app}\{#MyAppExeName}"; Flags: nowait skipifnotsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
