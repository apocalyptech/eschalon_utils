; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{0FCD12BE-F238-438E-BBC4-77FEEEE05DC3}
AppName=Eschalon Utilities
AppVerName=Eschalon Utilities 0.6.2
AppPublisher=CJ Kucera
AppPublisherURL=http://apocalyptech.com/eschalon/
AppSupportURL=http://apocalyptech.com/eschalon/
AppUpdatesURL=http://apocalyptech.com/eschalon/
DefaultDirName={pf}\Eschalon Utilities
DefaultGroupName=Eschalon Utilities
AllowNoIcons=yes
LicenseFile=C:\InstPrograms\eschalon_utils\COPYING.txt
InfoBeforeFile=C:\InstPrograms\eschalon_utils\README.txt
OutputBaseFilename=eschalon_utils_0_6_2_setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
;Source: "C:\InstPrograms\eschalon\dist\eschalon_b1_char.exe"; DestDir: "{app}"; Flags: ignoreversion
;Source: "C:\InstPrograms\eschalon\dist\eschalon_b1_map.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\InstPrograms\eschalon_utils\dist\*"; DestDir: {app}; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Book 1 Character Editor"; Filename: "{app}\eschalon_b1_char.exe"
Name: "{group}\Book 1 Map Editor"; Filename: "{app}\eschalon_b1_map.exe"
Name: "{group}\Book 2 Character Editor"; Filename: "{app}\eschalon_b2_char.exe"
Name: "{group}\Uninstall Eschalon Utilities"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\eschalon_b1_char.exe"; Description: "{cm:LaunchProgram,Eschalon Book I Character Editor}"; Flags: nowait postinstall skipifsilent


