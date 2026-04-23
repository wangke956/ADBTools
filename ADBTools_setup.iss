; Inno Setup 安装脚本 - ADBTools 打包
; 用于打包 dist_nuitka 文件夹内容（Nuitka standalone 模式）

#define MyAppName "ADBTools"
#define MyAppVersion "1.8.21"
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
; 权限设置 - 改为需要管理员权限以确保写入权限
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; 安装后自动创建用户数据目录
ChangesAssociations=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面图标(&D)"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动图标(&Q)"; GroupDescription: "附加图标:"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; 主程序文件
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Python 运行时库
Source: "{#SourceDir}\python310.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\python3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\pythoncom310.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\pywintypes310.dll"; DestDir: "{app}"; Flags: ignoreversion

; Visual C++ 运行时库
Source: "{#SourceDir}\vcruntime140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\vcruntime140_1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\msvcp140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\msvcp140_1.dll"; DestDir: "{app}"; Flags: ignoreversion

; OpenSSL 库
Source: "{#SourceDir}\libcrypto-1_1-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\libssl-1_1-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\libcrypto-3-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\libssl-3-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\libeay32.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\ssleay32.dll"; DestDir: "{app}"; Flags: ignoreversion

; 其他系统库
Source: "{#SourceDir}\ffi.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\libbz2.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\liblzma.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\zlib.dll"; DestDir: "{app}"; Flags: ignoreversion

; Python 扩展模块 (.pyd 文件)
Source: "{#SourceDir}\*.pyd"; DestDir: "{app}"; Flags: ignoreversion

; UI 和配置文件
Source: "{#SourceDir}\adbtool.ui"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\file_manager_ui.ui"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\adbtools_config.json"; DestDir: "{app}"; Flags: ignoreversion
; 注意: command_history.log 是运行时生成的日志文件，不需要打包

; 图标文件
Source: "{#SourceDir}\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; PyQt5 相关文件和插件（包含 Qt5 子目录）
Source: "{#SourceDir}\PyQt5\*"; DestDir: "{app}\PyQt5"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\qt5*.dll"; DestDir: "{app}"; Flags: ignoreversion

; uiautomator2 资源文件
Source: "{#SourceDir}\uiautomator2\*"; DestDir: "{app}\uiautomator2"; Flags: ignoreversion recursesubdirs createallsubdirs

; adbutils 二进制文件（包含 adb.exe 等）
Source: "{#SourceDir}\adbutils\*"; DestDir: "{app}\adbutils"; Flags: ignoreversion recursesubdirs createallsubdirs

; apkutils 数据文件
Source: "{#SourceDir}\apkutils\*"; DestDir: "{app}\apkutils"; Flags: ignoreversion recursesubdirs createallsubdirs

; certifi 证书文件
Source: "{#SourceDir}\certifi\*"; DestDir: "{app}\certifi"; Flags: ignoreversion recursesubdirs createallsubdirs

; charset_normalizer 模块
Source: "{#SourceDir}\charset_normalizer\*"; DestDir: "{app}\charset_normalizer"; Flags: ignoreversion recursesubdirs createallsubdirs

; cryptography 模块
Source: "{#SourceDir}\cryptography\*"; DestDir: "{app}\cryptography"; Flags: ignoreversion recursesubdirs createallsubdirs

; jaraco 文本数据
Source: "{#SourceDir}\jaraco\*"; DestDir: "{app}\jaraco"; Flags: ignoreversion recursesubdirs createallsubdirs

; lxml 模块
Source: "{#SourceDir}\lxml\*"; DestDir: "{app}\lxml"; Flags: ignoreversion recursesubdirs createallsubdirs

; markupsafe 模块
Source: "{#SourceDir}\markupsafe\*"; DestDir: "{app}\markupsafe"; Flags: ignoreversion recursesubdirs createallsubdirs

; PIL/Pillow 图像处理库
Source: "{#SourceDir}\PIL\*"; DestDir: "{app}\PIL"; Flags: ignoreversion recursesubdirs createallsubdirs

; psutil 系统监控模块
Source: "{#SourceDir}\psutil\*"; DestDir: "{app}\psutil"; Flags: ignoreversion recursesubdirs createallsubdirs

; pytz 时区数据
Source: "{#SourceDir}\pytz\*"; DestDir: "{app}\pytz"; Flags: ignoreversion recursesubdirs createallsubdirs

; zstandard 压缩库
Source: "{#SourceDir}\zstandard\*"; DestDir: "{app}\zstandard"; Flags: ignoreversion recursesubdirs createallsubdirs

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
    // 创建用户数据目录
    if not DirExists(ExpandConstant('{userappdata}\ADBTools')) then
    begin
      if not CreateDir(ExpandConstant('{userappdata}\ADBTools')) then
      begin
        MsgBox('警告：无法创建用户数据目录 ' + ExpandConstant('{userappdata}\ADBTools') + '，日志可能无法正常保存。', mbError, MB_OK);
      end
      else
      begin
        MsgBox('已创建用户数据目录: ' + ExpandConstant('{userappdata}\ADBTools'), mbInformation, MB_OK);
      end;
    end;
    
    // 可以在这里添加其他初始化操作
    // 例如：创建配置文件、注册表设置等
  end;
end;