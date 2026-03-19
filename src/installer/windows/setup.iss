; Inno Setup Script for Agent Environment Launcher
; Generated for INS-005 — wraps PyInstaller --onedir output

#define MyAppName "Agent Environment Launcher"
#define MyAppVersion "3.0.2"
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
; INS-021: Deploy the ts-python Windows shim to the well-known user-local bin
; directory.  ignoreversion ensures reinstall/update overwrites the shim.
Source: "..\..\installer\shims\ts-python.cmd"; DestDir: "{localappdata}\TurbulenceSolutions\bin"; Flags: ignoreversion

[Registry]
; INS-021: Append %LOCALAPPDATA%\TurbulenceSolutions\bin to the current user's
; PATH so that ts-python is available from any new terminal after install.
; NeedsAddPath() prevents duplicate entries on reinstall or update.
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{localappdata}\TurbulenceSolutions\bin"; Check: NeedsAddPath(ExpandConstant('{localappdata}\TurbulenceSolutions\bin'))

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
; INS-021: Remove the entire user-local TurbulenceSolutions config directory
; (contains bin\ts-python.cmd and python-path.txt) on uninstall.
Type: filesandordirs; Name: "{localappdata}\TurbulenceSolutions"

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

// INS-021: Return True when PathToAdd is not already present in the current
// user's PATH registry value.  The check is case-insensitive and uses semicolon
// wrapping so a partial substring cannot produce a false positive.
function NeedsAddPath(PathToAdd: String): Boolean;
var
  OldPath: String;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', OldPath) then
  begin
    Result := True;
    Exit;
  end;
  Result := (Pos(';' + Lowercase(PathToAdd) + ';',
                 ';' + Lowercase(OldPath) + ';') = 0);
end;

// INS-021: After all files are installed, write python-path.txt so the
// ts-python shim knows where to find the bundled Python executable.
// Using Append=False overwrites any existing file, which handles
// reinstall/update where {app} may have changed.
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir: String;
  ConfigFile: String;
  PythonPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigDir := ExpandConstant('{localappdata}\TurbulenceSolutions');
    ConfigFile := ConfigDir + '\python-path.txt';
    PythonPath := ExpandConstant('{app}\python-embed\python.exe');
    if not DirExists(ConfigDir) then
      CreateDir(ConfigDir);
    SaveStringToFile(ConfigFile, PythonPath, False);
  end;
end;

// INS-021: On uninstall, remove %LOCALAPPDATA%\TurbulenceSolutions\bin from
// the user PATH registry value so no dead entry lingers after removal.
// [UninstallDelete] removes the files; this procedure removes the PATH entry.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  OldPath: String;
  BinDir: String;
  OldPathWrapped: String;
  LowerOldPath: String;
  LowerSearch: String;
  StartPos: Integer;
  NewPath: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    BinDir := ExpandConstant('{localappdata}\TurbulenceSolutions\bin');
    if not RegQueryStringValue(HKCU, 'Environment', 'Path', OldPath) then
      Exit;
    // Wrap with semicolons for reliable case-insensitive substring matching.
    OldPathWrapped := ';' + OldPath + ';';
    LowerOldPath := Lowercase(OldPathWrapped);
    LowerSearch := ';' + Lowercase(BinDir) + ';';
    StartPos := Pos(LowerSearch, LowerOldPath);
    if StartPos = 0 then
      Exit;
    // Remove ';BinDir' (StartPos … StartPos+Length(BinDir)) from wrapped string.
    Delete(OldPathWrapped, StartPos, Length(BinDir) + 1);
    // Strip leading/trailing semicolons left by the removal.
    NewPath := OldPathWrapped;
    while (Length(NewPath) > 0) and (NewPath[1] = ';') do
      Delete(NewPath, 1, 1);
    while (Length(NewPath) > 0) and (NewPath[Length(NewPath)] = ';') do
      Delete(NewPath, Length(NewPath), 1);
    RegWriteExpandStringValue(HKCU, 'Environment', 'Path', NewPath);
  end;
end;
