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
; INS-018: Bundle the Python embeddable distribution so the security gate can
; run without requiring the user to have Python installed separately.
; The python-embed\ directory is populated at CI build time by downloading
; python-3.11.x-embed-amd64.zip from python.org and extracting it into
; src\installer\python-embed\ before running PyInstaller and iscc.
Source: "..\python-embed\*"; DestDir: "{app}\python-embed"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: PythonEmbedExists

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
; INS-018: Remove the bundled Python embeddable directory on uninstall.
Type: filesandordirs; Name: "{app}\python-embed"

[Code]
// INS-018: Return True only when the python-embed source directory contains
// python.exe, meaning the CI build step has already extracted the embeddable
// package.  Without this guard iscc would fail when run in a plain developer
// environment where the ~15 MB binary distribution has not been downloaded.
function PythonEmbedExists(): Boolean;
var
  SrcDir: String;
begin
  SrcDir := ExpandConstant('{src}') + '\..\python-embed\python.exe';
  Result := FileExists(SrcDir);
end;
