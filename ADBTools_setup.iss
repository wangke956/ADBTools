; Inno Setup 安装脚本 - ADBTools 打包
; 用于打包 dist_nuitka 文件夹内容（Nuitka standalone 模式）

#define MyAppName "ADBTools"
#define MyAppVersion "1.8.32"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://example.com/"
#define MyAppExeName "ADBTools_nuitka.exe"
#define SourceDir "dist_nuitka"

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
; 权限设置 - 普通用户权限即可安装，不强制要求管理员（受限电脑可正常安装）
; 如需安装到 Program Files 等受保护目录，可在安装向导中手动提权
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes

[Languages]
; 注释掉中文语言支持，因为 GitHub Actions 预装的 Inno Setup 可能不包含该语言文件
; Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面图标(&D)"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动图标(&Q)"; GroupDescription: "附加图标:"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Dirs]
; 预创建日志目录，运行时日志统一写入安装目录下的 logs，不再依赖C盘用户目录
; Permissions: users-modify —— 确保安装到 Program Files 时 Users 组也有写入权限
; uninsalwaysuninstall —— 卸载时一并删除（日志不保留）
Name: "{app}\logs"; Permissions: users-modify; Flags: uninsalwaysuninstall

[Files]
; 主程序文件（Nuitka OneFile 模式已将所有 DLL 打包到 exe 中）
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; UI 和配置文件
Source: "{#SourceDir}\adbtool.ui"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\file_manager_ui.ui"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\adbtools_config.json"; DestDir: "{app}"; Flags: ignoreversion
; 注意: command_history.log 是运行时生成的日志文件，不需要打包

; 图标文件
Source: "{#SourceDir}\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; uiautomator2 资源文件（Nuitka OneFile 模式不会自动包含，需手动复制）
Source: "{#SourceDir}\uiautomator2\*"; DestDir: "{app}\uiautomator2"; Flags: ignoreversion recursesubdirs createallsubdirs

; adbutils 二进制文件（包含 adb.exe 等，Nuitka OneFile 模式不会自动包含，需手动复制）
Source: "{#SourceDir}\adbutils\*"; DestDir: "{app}\adbutils"; Flags: ignoreversion recursesubdirs createallsubdirs

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

// 安装完成后修正 logs 目录权限：
// Inno Setup 的 [Dirs] Permissions 参数仅在创建目录时生效，
// 升级安装时如果 logs 目录已存在（旧版本遗留），ACL 不会被更新，
// 导致普通用户运行 exe 时无法写入日志。此处显式调用 icacls 兜底修复。
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  LogsDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    LogsDir := ExpandConstant('{app}\logs');
    if DirExists(LogsDir) then
    begin
      // 使用 SID *S-1-5-32-545 (BUILTIN\Users) 避免中英文系统名称差异
      // (OI)(CI)M = 对象继承 + 容器继承 + Modify 权限
      Exec('icacls.exe', '"' + LogsDir + '" /grant "*S-1-5-32-545:(OI)(CI)M" /T',
           '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      // icacls 失败不阻断安装，运行时 logger_manager 会自动回退到 %LOCALAPPDATA%\ADBTools\logs
    end;
  end;
end;

// 安装完成后无需额外初始化：
// 日志目录已在 [Dirs] 中预创建并授予 Users 修改权限，
// 运行时日志统一写入安装目录下的 logs，不再往 %APPDATA% 创建用户数据目录，
// 避免C盘权限受限导致的问题