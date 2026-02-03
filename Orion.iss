; Orion Installer Script for Inno Setup
; Created by Gemini Code Assist

#define MyAppVersion "1.3.5"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{F4B6E3A1-5B9A-4A8D-9B3A-1C2D3E4F5A6B}
AppName=Orion AI Chatbot
AppVersion={#MyAppVersion}
AppPublisher=OmniNode
DefaultDirName={autopf}\Orion
DefaultGroupName=Orion AI Chatbot
AllowNoIcons=yes
OutputBaseFilename=Orion_Setup_{#MyAppVersion}
OutputDir=Output_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern windows11
PrivilegesRequired=admin
SetupIconFile=logo.ico
WizardSmallImageFile=logo.png
ChangesAssociations=yes
LicenseFile=terms_of_use.txt
InfoBeforeFile=privacy_policy.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "changelog.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't ship user settings, but you could ship a default template.
; Source: "orion_settings.json"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
Root: HKCR; Subkey: ".orion"; ValueType: string; ValueName: ""; ValueData: "OrionChatFile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "OrionChatFile"; ValueType: string; ValueName: ""; ValueData: "Orion Chat File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "OrionChatFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\logo.ico"
Root: HKCR; Subkey: "OrionChatFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Orion.exe"" ""%1"""

[Icons]
Name: "{group}\Orion AI Chatbot"; Filename: "{app}\Orion.exe"; IconFilename: "{app}\logo.ico"
Name: "{group}\{cm:UninstallProgram,Orion AI Chatbot}"; Filename: "{uninstallexe}"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\Orion AI Chatbot"; Filename: "{app}\Orion.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\Orion.exe"; Description: "{cm:LaunchProgram,Orion AI Chatbot}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\changelog.txt"
Type: filesandordirs; Name: "{localappdata}\.orion"

[Code]
// System RAM detection kept for potential future use or analytics
type
  TMemoryStatusEx = record
    dwLength: DWORD;
    dwMemoryLoad: DWORD;
    ullTotalPhys: Int64;
    ullAvailPhys: Int64;
    ullTotalPageFile: Int64;
    ullAvailPageFile: Int64;
    ullTotalVirtual: Int64;
    ullAvailVirtual: Int64;
    ullAvailExtendedVirtual: Int64;
  end;

function GlobalMemoryStatusEx(var lpBuffer: TMemoryStatusEx): BOOL;
external 'GlobalMemoryStatusEx@kernel32.dll stdcall';

function GetSystemRAM: Int64;
var
  MemStatus: TMemoryStatusEx;
begin
  MemStatus.dwLength := SizeOf(MemStatus);
  if GlobalMemoryStatusEx(MemStatus) then
    Result := MemStatus.ullTotalPhys
  else
    Result := 0;
end;

procedure InitializeWizard;
begin
  // RAM detection simplified
end;
