; ---------------------------------------------------------
; JK Draw - Inno Setup installer
;
; Online-installer: indeholder selve programmet, men finder/installerer
; Python (via winget, med fallback til direkte download fra python.org)
; og de noedvendige pip-pakker under installationen, med en rigtig
; fremgangsbjaelke i stedet for et konsolvindue.
; ---------------------------------------------------------

#define MyAppName "JK Draw"
#define MyAppVersion "1.1.1"
#define MyAppPublisher "Jonas Krohn"
#define MyPythonVersion "3.12.2"
#define MyWingetId "Python.Python.3.12"

[Setup]
AppId={{DAA91F62-FBD8-4BBB-9ABC-1C57E7D57A8D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\JK Draw
DefaultGroupName=JK Draw
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=JKDraw-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\start.ico
UninstallDisplayIcon={app}\start.ico

[Languages]
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"

[Tasks]
Name: "desktopicon"; Description: "Opret en genvej paa skrivebordet"; GroupDescription: "Yderligere genveje:"

[Files]
Source: "..\src\*"; DestDir: "{app}\src"; Flags: recursesubdirs createallsubdirs ignoreversion; Excludes: "__pycache__\*"
Source: "..\version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\update_checker.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README_DK.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README_EN.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\start.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\JK Draw"; Filename: "{code:GetPythonwPath}"; Parameters: "main.py"; WorkingDir: "{app}\src"; IconFilename: "{app}\start.ico"
Name: "{autodesktop}\JK Draw"; Filename: "{code:GetPythonwPath}"; Parameters: "main.py"; WorkingDir: "{app}\src"; Tasks: desktopicon; IconFilename: "{app}\start.ico"

[Run]
Filename: "{code:GetPythonwPath}"; Parameters: "main.py"; WorkingDir: "{app}\src"; Description: "Start JK Draw nu"; Flags: nowait postinstall skipifsilent

[Code]
var
  PythonExePath: String;

{ ---------------------------------------------------------
  Hjaelpefunktion: koer et program skjult og returner ResultCode
  --------------------------------------------------------- }
function RunHidden(const Filename, Params, WorkDir: String; var ResultCode: Integer): Boolean;
begin
  Result := Exec(Filename, Params, WorkDir, SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

{ ---------------------------------------------------------
  Koer et program med administrator-rettigheder (UAC-prompt)
  --------------------------------------------------------- }
function RunElevated(const Filename, Params, WorkDir: String; var ResultCode: Integer): Boolean;
begin
  Result := ShellExec('runas', Filename, Params, WorkDir, SW_SHOW, ewWaitUntilTerminated, ResultCode);
end;

{ ---------------------------------------------------------
  Koer skjult uden admin - hvis det fejler, spoerg brugeren om
  at forsoege igen med administrator-rettigheder i stedet for
  bare at fejle.
  --------------------------------------------------------- }
function RunHiddenWithElevationFallback(const Filename, Params, WorkDir, FailureContext: String): Boolean;
var
  ResultCode: Integer;
begin
  Result := RunHidden(Filename, Params, WorkDir, ResultCode) and (ResultCode = 0);
  if Result then
    Exit;

  if SuppressibleMsgBox(
       FailureContext + #13#10#13#10 +
       'Dette skyldes ofte manglende rettigheder.' + #13#10 +
       'Vil du give administrator-rettigheder og forsoege igen?',
       mbConfirmation, MB_YESNO, IDYES) = IDYES then
  begin
    Result := RunElevated(Filename, Params, WorkDir, ResultCode) and (ResultCode = 0);
  end;
end;

function CommandExists(const CmdName: String): Boolean;
var
  ResultCode: Integer;
begin
  Result := RunHidden(ExpandConstant('{cmd}'), '/C where ' + CmdName + ' >nul 2>&1', '', ResultCode)
            and (ResultCode = 0);
end;

{ ---------------------------------------------------------
  Forsoeg at finde en allerede installeret Python
  --------------------------------------------------------- }
function FindPythonExe(): String;
var
  ResultCode: Integer;
  TmpFile: String;
  Lines: TArrayOfString;
  Candidates: TArrayOfString;
  i: Integer;
begin
  Result := '';

  { 1) Velkendte per-bruger installationsstier (winget/python.org installerer hertil) }
  SetArrayLength(Candidates, 4);
  Candidates[0] := ExpandConstant('{localappdata}\Programs\Python\Python312\python.exe');
  Candidates[1] := ExpandConstant('{localappdata}\Programs\Python\Python311\python.exe');
  Candidates[2] := ExpandConstant('{localappdata}\Programs\Python\Python310\python.exe');
  Candidates[3] := ExpandConstant('{localappdata}\Programs\Python\Python313\python.exe');

  for i := 0 to GetArrayLength(Candidates) - 1 do
  begin
    if FileExists(Candidates[i]) then
    begin
      Result := Candidates[i];
      Exit;
    end;
  end;

  { 2) Fald tilbage til PATH via "where" }
  TmpFile := ExpandConstant('{tmp}\where_python.txt');
  if RunHidden(ExpandConstant('{cmd}'), '/C where python > "' + TmpFile + '" 2>nul', '', ResultCode) then
  begin
    if (ResultCode = 0) and FileExists(TmpFile) then
    begin
      if LoadStringsFromFile(TmpFile, Lines) and (GetArrayLength(Lines) > 0) then
        Result := Trim(Lines[0]);
    end;
  end;
end;

{ ---------------------------------------------------------
  Opdater den indbyggede installations-fremgangsbjaelke
  --------------------------------------------------------- }
procedure UpdateProgress(const Status: String; Position, Max: Integer);
begin
  WizardForm.StatusLabel.Caption := Status;
  if Max < 1 then
    Max := 1;
  WizardForm.ProgressGauge.Max := Max;
  WizardForm.ProgressGauge.Position := Position;
  WizardForm.Update;
end;

{ ---------------------------------------------------------
  Installer Python via winget (kraever ikke administrator)
  --------------------------------------------------------- }
function InstallPythonViaWinget(): Boolean;
begin
  Result := False;

  if not CommandExists('winget') then
  begin
    UpdateProgress('winget blev ikke fundet - forsoeger en anden metode...', 5, 100);
    Exit;
  end;

  UpdateProgress('Installerer Python via winget...', 10, 100);
  Result := RunHiddenWithElevationFallback(ExpandConstant('{cmd}'),
    '/C winget install --id ' + ExpandConstant('{#MyWingetId}') + ' -e --scope user --silent --accept-package-agreements --accept-source-agreements',
    '', 'Installation af Python via winget fejlede.');

  if not Result then
    UpdateProgress('winget-installationen fejlede - forsoeger en anden metode...', 5, 100);
end;

{ ---------------------------------------------------------
  Fallback: download og installer Python direkte fra python.org
  --------------------------------------------------------- }
function InstallPythonViaDirectDownload(): Boolean;
var
  ResultCode: Integer;
  InstallerPath: String;
  DownloadUrl: String;
begin
  Result := False;
  InstallerPath := ExpandConstant('{tmp}\python_installer.exe');
  DownloadUrl := 'https://www.python.org/ftp/python/' + ExpandConstant('{#MyPythonVersion}') +
                 '/python-' + ExpandConstant('{#MyPythonVersion}') + '-amd64.exe';

  UpdateProgress('Downloader Python fra python.org...', 10, 100);
  if not (RunHidden(ExpandConstant('{cmd}'),
       '/C curl -L -o "' + InstallerPath + '" ' + DownloadUrl,
       '', ResultCode) and (ResultCode = 0)) then
  begin
    SuppressibleMsgBox(
      'Kunne ikke downloade Python.' + #13#10 +
      'Dette skyldes oftest en firewall, der blokerer download af .exe-filer.' + #13#10#13#10 +
      'Installer venligst Python manuelt fra https://www.python.org/downloads/' + #13#10 +
      'og koer derefter denne installation igen.',
      mbError, MB_OK, IDOK);
    Exit;
  end;

  UpdateProgress('Installerer Python (kun for din egen bruger)...', 30, 100);
  if not RunHiddenWithElevationFallback(InstallerPath,
       'InstallAllUsers=0 InstallLauncherAllUsers=0 PrependPath=1 Include_pip=1', '',
       'Python-installationen fejlede.') then
  begin
    SuppressibleMsgBox(
      'Python-installationen fejlede.' + #13#10 +
      'Installer venligst Python manuelt fra https://www.python.org/downloads/' + #13#10 +
      'og koer derefter denne installation igen.',
      mbError, MB_OK, IDOK);
    Exit;
  end;

  Result := True;
end;

{ ---------------------------------------------------------
  Sikrer at Python findes - installerer hvis noedvendigt
  --------------------------------------------------------- }
procedure EnsurePythonInstalled;
begin
  UpdateProgress('Tjekker om Python er installeret...', 1, 100);
  PythonExePath := FindPythonExe();

  if PythonExePath <> '' then
  begin
    UpdateProgress('Python fundet.', 10, 100);
    Exit;
  end;

  UpdateProgress('Python blev ikke fundet - forsoeger installation...', 5, 100);

  if InstallPythonViaWinget() then
    PythonExePath := FindPythonExe();

  if PythonExePath = '' then
  begin
    if InstallPythonViaDirectDownload() then
      PythonExePath := FindPythonExe();
  end;

  if PythonExePath = '' then
  begin
    SuppressibleMsgBox(
      'Python kunne ikke installeres automatisk.' + #13#10 +
      'Installer venligst Python manuelt fra https://www.python.org/downloads/' + #13#10 +
      'og koer derefter denne installation igen.',
      mbError, MB_OK, IDOK);
  end;
end;

{ ---------------------------------------------------------
  Installer pakkerne fra requirements.txt, en for en, med
  fremgang i den indbyggede installations-fremgangsbjaelke
  --------------------------------------------------------- }
procedure InstallRequirements;
var
  ReqFile: String;
  Lines: TArrayOfString;
  i, Total: Integer;
  Pkg: String;
begin
  ReqFile := ExpandConstant('{app}\src\requirements.txt');
  if not FileExists(ReqFile) then
    Exit;

  if not LoadStringsFromFile(ReqFile, Lines) then
    Exit;

  Total := GetArrayLength(Lines);
  if Total = 0 then
    Exit;

  UpdateProgress('Opdaterer pip...', 0, Total);
  RunHiddenWithElevationFallback(PythonExePath, '-m pip install --upgrade pip', '',
    'Kunne ikke opdatere pip.');

  { Seed update_checker.py's lokale requirements-cache, saa fremtidige
    selv-opdateringer kun geninstallerer pakker naar src/requirements.txt
    rent faktisk aendrer sig. }
  CopyFile(ReqFile, ExpandConstant('{app}\requirements.txt'), False);

  for i := 0 to Total - 1 do
  begin
    Pkg := Trim(Lines[i]);
    if Pkg = '' then
      Continue;

    UpdateProgress('Installerer pakke ' + IntToStr(i + 1) + ' / ' + IntToStr(Total) + ': ' + Pkg, i, Total);

    if not RunHiddenWithElevationFallback(PythonExePath, '-m pip install ' + Pkg, '',
         'Kunne ikke installere pakken "' + Pkg + '".') then
    begin
      SuppressibleMsgBox(
        'Kunne ikke installere pakken "' + Pkg + '".' + #13#10 +
        'Dette skyldes oftest ingen internetforbindelse, eller en firewall der' + #13#10 +
        'blokerer adgang til pypi.org.' + #13#10#13#10 +
        'Programmet kan stadig fungere, men funktioner der bruger denne pakke vil fejle.',
        mbError, MB_OK, IDOK);
    end;
  end;

  UpdateProgress('Alle pakker installeret.', Total, Total);
end;

{ ---------------------------------------------------------
  Wizard-konstant: stien til pythonw.exe (bruges i [Icons]/[Run])
  --------------------------------------------------------- }
function GetPythonwPath(Param: String): String;
begin
  if PythonExePath <> '' then
    Result := ExtractFilePath(PythonExePath) + 'pythonw.exe'
  else
    Result := 'pythonw.exe';
end;

{ ---------------------------------------------------------
  Installations-hooks
  --------------------------------------------------------- }
procedure CurStepChanged(CurStep: TSetupStep);
begin
  { Foer filer/ikoner oprettes: sikr at Python findes, saa GetPythonwPath
    kan finde den korrekte sti naar [Icons] behandles. }
  if CurStep = ssInstall then
    EnsurePythonInstalled;

  { Efter filer er kopieret (requirements.txt findes nu): installer pakker. }
  if CurStep = ssPostInstall then
  begin
    if PythonExePath <> '' then
      InstallRequirements;
  end;
end;
