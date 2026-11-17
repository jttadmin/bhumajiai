[Setup]
AppId=BhumajiAI.Desktop
AppName=BhumajiAI
AppVersion=4.0.0
AppPublisher=BhumajiAI
DefaultDirName={localappdata}\Programs\BhumajiAI
DefaultGroupName=BhumajiAI
PrivilegesRequired=lowest
OutputDir=..\installer-output
OutputBaseFilename=BhumajiAI-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\BhumajiAI.exe
[Files]
Source: "..\dist\BhumajiAI.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\BhumajiAI"; Filename: "{app}\BhumajiAI.exe"
Name: "{autodesktop}\BhumajiAI"; Filename: "{app}\BhumajiAI.exe"
[Run]
Filename: "{app}\BhumajiAI.exe"; Description: "Launch BhumajiAI"; Flags: nowait postinstall skipifsilent
