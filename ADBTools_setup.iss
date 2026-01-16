; Inno Setup 安装脚本 - ADBTools 打包
; 用于打包 build_nuitka 文件夹内容

#define MyAppName "ADBTools"
#define MyAppVersion "1.6.3"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://example.com/"
#define MyAppExeName "ADBTools_nuitka.exe"
#define SourceDir "build_nuitka"

[Setup]
; 注意: AppId 的值在每次发布新版本时不应更改
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; 卸载程序信息
UninstallDisplayIcon={app}\{#MyAppExeName}
; 安装程序图标
SetupIconFile=icon.ico
; 压缩设置
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; 输出设置
OutputDir=Output
OutputBaseFilename=ADBTools_Setup
; 权限设置
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面图标(&D)"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动图标(&Q)"; GroupDescription: "附加图标:"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; 主程序文件
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; ADB 工具文件
Source: "{#SourceDir}\adb.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\AdbWinApi.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\AdbWinUsbApi.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\fastboot.exe"; DestDir: "{app}"; Flags: ignoreversion
; 其他工具文件
Source: "{#SourceDir}\aapt.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\etc1tool.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\hprof-conv.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\make_f2fs.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\make_f2fs_casefold.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\mke2fs.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\sqlite3.exe"; DestDir: "{app}"; Flags: ignoreversion
; 配置文件和资源文件
Source: "{#SourceDir}\adbtool.ui"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\adbtools_config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\libwinpthread-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\mke2fs.conf"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\NOTICE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\source.properties"; DestDir: "{app}"; Flags: ignoreversion
; 图标文件（如果存在）
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists('icon.ico')

; 注意: 以下行用于包含所有文件，但上面已经列出了具体文件，所以注释掉
; Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// 自定义函数：检查是否安装了必要的运行时库
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // 可以在这里添加检查.NET Framework或其他运行时库的代码
  // 例如：
  // if not IsDotNetInstalled('...') then begin
  //   MsgBox('需要安装 .NET Framework X.X', mbError, MB_OK);
  //   Result := False;
  // end;
end;

// 安装完成后显示提示信息
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 可以在这里添加安装完成后的操作
    // 例如：创建配置文件、注册表设置等
  end;
end;