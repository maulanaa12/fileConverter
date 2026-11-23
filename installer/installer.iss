; Script Inno Setup untuk LocalPDF Studio
; Menghasilkan installer dengan nomor versi pada nama file.

#define MyAppName "LocalPDF Studio"
#define MyAppVersion "1.2.2"
#define MyAppPublisher "LocalPDF Studio"
#define MyAppURL "https://github.com"
#define MyAppExeName "LocalPDFStudio.exe"

[Setup]
; Identifikasi Aplikasi
AppId={{D828C5A4-9F22-4D3B-BA7E-7F899D2A1C30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
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
OutputBaseFilename=LocalPDF_Studio_Setup_{#MyAppVersion}
SetupIconFile=..\static\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
RedirectionGuard=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Seluruh isi folder dist/LocalPDFStudio
Source: "..\dist\LocalPDFStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
