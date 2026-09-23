; Script Inno Setup untuk LocalPDF Studio
; Menghasilkan file installer tunggal: LocalPDF_Studio_Setup.exe

#define MyAppName "LocalPDF Studio"
#define MyAppVersion "1.2.1"
#define MyAppPublisher "LocalPDF Studio"
#define MyAppURL "https://github.com"
#define MyAppExeName "LocalPDFStudio.exe"

[Setup]
; Identifikasi Aplikasi
AppId={{D828C5A4-9F22-4D3B-BA7E-7F899D2A1C30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Pengaturan Kompresi Terbaik
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir=output
OutputBaseFilename=LocalPDF_Studio_Setup
SetupIconFile=..\static\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Seluruh isi folder dist/LocalPDFStudio
Source: "..\dist\LocalPDFStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\static\app_icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
; Desktop shortcut is created via [Code] to handle OneDrive permission errors gracefully

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  DesktopPath: String;
  ShortcutPath: String;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('desktopicon') then
  begin
    DesktopPath := ExpandConstant('{autodesktop}');
    ShortcutPath := DesktopPath + '\{#MyAppName}.lnk';
    try
      CreateShellLink(
        ShortcutPath,
        '',
        ExpandConstant('{app}\{#MyAppExeName}'),
        '',
        ExpandConstant('{app}'),
        ExpandConstant('{app}\static\app_icon.ico'),
        0,
        SW_SHOWNORMAL);
    except
      MsgBox('Desktop shortcut could not be created because the Desktop folder is managed by OneDrive or access was denied.' + #13#10 + #13#10 +
             'The application has been installed successfully. You can launch it from the Start Menu.',
             mbInformation, MB_OK);
    end;
  end;
end;
