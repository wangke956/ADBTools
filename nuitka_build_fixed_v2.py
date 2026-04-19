#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuitka打包配置文件 - 修复版本
用于将ADBTools打包为独立的可执行文件

使用方法:
python nuitka_build_fixed_v2.py --build  # 构建可执行文件
python nuitka_build_fixed_v2.py --clean  # 清理构建文件
python nuitka_build_fixed_v2.py --help   # 显示帮助信息
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 构建配置
CONFIG = {
    "main_script": "main.py",
    "output_name": "ADBTools_nuitka",
    "icon": "icon.ico",
    "company_name": "ADBTools",
    "product_name": "ADBTools",
    # 版本号将从config_manager动态获取
    "file_version": "",  # 将在get_nuitka_command中动态设置
    "product_version": "",  # 将在get_nuitka_command中动态设置
    "copyright": "Copyright © 2024 ADBTools. All rights reserved.",
    "description": "ADB Tools - Android Debug Bridge GUI Tool",
    
    # 依赖文件
    "data_files": [
        ("adbtool.ui", "."),
        ("file_manager_ui.ui", "."),
        ("adbtools_config.json", "."),
        ("icon.ico", "."),
    ],
    
    # 需要包含的Python模块
    "include_modules": [
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtWidgets",
        "PyQt5.QtGui",
        "qdarkstyle",
        "uiautomator2",
        "adbutils",
        "configparser",
        "openpyxl",
        "psutil",
        "lxml",
    ],
    
    # 需要排除的模块（减小体积和编译时间）
    "exclude_modules": [
        "matplotlib",
        "scipy",
        "numpy",
        "pandas",
        "IPython",
        "jedi",
        "pygments",
        "sqlalchemy",
        "test",
        "unittest",
        "tkinter",
        "idlelib",
        "distutils",
        "setuptools",
        "pip",
        "ensurepip",
        "venv",
        "lib2to3",
        "ctypes.test",
        "email.test",
        "json.tests",
        "sqlite3.test",
        "tkinter.test",
        "unittest.test",
        "xmlrpc.test",
    ],
    
    # 插件
    "plugins": [
        "pyqt5",
        "tk-inter",
    ],
    
    # 构建目录
    "build_dir": PROJECT_ROOT / "build_nuitka",
    "dist_dir": PROJECT_ROOT / "dist_nuitka",
}


def get_nuitka_command(build_type="onefile"):
    """生成Nuitka构建命令"""
    
    # 从config_manager获取版本号
    try:
        from config_manager import config_manager
        file_version = config_manager.get_file_version()
        product_version = config_manager.get_version()
    except ImportError:
        # 如果config_manager不可用，使用默认版本
        file_version = "1.5.0.0"
        product_version = "1.5.0"
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--remove-output",
        "--assume-yes-for-downloads",
        "--plugin-enable=pyqt5",
        # 性能优化：使用所有CPU核心进行并行编译
        "--jobs=" + str(os.cpu_count()),
        # 性能优化：启用 LTO 加速链接
        "--lto=yes",
        "--windows-icon-from-ico=" + str(PROJECT_ROOT / CONFIG["icon"]),
        "--company-name=" + CONFIG["company_name"],
        "--product-name=" + CONFIG["product_name"],
        "--file-version=" + file_version,
        "--product-version=" + product_version,
        "--file-description=" + CONFIG["description"],
        "--copyright=" + CONFIG["copyright"],
        "--output-dir=" + str(CONFIG["build_dir"]),
        "--output-filename=" + CONFIG["output_name"],
    ]
    
    # 添加包含模块
    for module in CONFIG["include_modules"]:
        cmd.append(f"--include-module={module}")
    
    # 添加排除模块
    for module in CONFIG["exclude_modules"]:
        cmd.append(f"--nofollow-import-to={module}")
    
    # 单文件模式
    if build_type == "onefile":
        cmd.append("--onefile")
        cmd.append("--windows-console-mode=disable")
    else:
        cmd.append("--windows-console-mode=disable")
    
    # 添加数据文件
    for src, dst in CONFIG["data_files"]:
        src_path = PROJECT_ROOT / src
        if src_path.exists():
            # 如果目标路径是'.'，则使用源文件名
            if dst == ".":
                dst = src
            cmd.append(f"--include-data-files={src_path}={dst}")
        else:
            print(f"警告: 数据文件不存在: {src_path}")
    
    # 添加Function_Moudle目录
    function_module_dir = PROJECT_ROOT / "Function_Moudle"
    if function_module_dir.exists():
        cmd.append(f"--include-package-data=Function_Moudle")
    
    # 添加ADB工具文件（如果存在）
    adb_files_to_check = [
        "adb.exe",
        "AdbWinApi.dll", 
        "AdbWinUsbApi.dll",
        "aapt.exe",
        "fastboot.exe",
    ]
    
    for adb_file in adb_files_to_check:
        adb_path = PROJECT_ROOT / adb_file
        if adb_path.exists():
            cmd.append(f"--include-data-files={adb_path}={adb_file}")
    
    # 添加uiautomator2的assets目录文件
    u2_assets_dir = PROJECT_ROOT / ".venv" / "Lib" / "site-packages" / "uiautomator2" / "assets"
    if u2_assets_dir.exists():
        # 复制所有assets文件，确保完整性
        import shutil
        
        # 复制到 dist_nuitka 目录
        dist_assets_dir = PROJECT_ROOT / "dist_nuitka" / "uiautomator2" / "assets"
        if dist_assets_dir.exists():
            shutil.rmtree(dist_assets_dir)
        dist_assets_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(u2_assets_dir, dist_assets_dir)
        print(f"已复制 uiautomator2 assets 目录到: {dist_assets_dir}")
        
        # 复制到 build_nuitka 目录（重要！Nuitka打包时会从这里读取资源）
        build_assets_dir = CONFIG["build_dir"] / "uiautomator2" / "assets"
        if build_assets_dir.exists():
            shutil.rmtree(build_assets_dir)
        build_assets_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(u2_assets_dir, build_assets_dir)
        print(f"已复制 uiautomator2 assets 目录到: {build_assets_dir}")
        
        # 添加到Nuitka构建命令（使用相对路径）
        cmd.append(f"--include-package-data=uiautomator2")
        
        # 列出复制的文件
        copied_files = list(dist_assets_dir.rglob("*"))
        copied_files = [f for f in copied_files if f.is_file()]
        print(f"已包含 {len(copied_files)} 个uiautomator2 assets文件")
        
        # 验证关键文件
        critical_files = ["u2.jar", "app-uiautomator.apk", "version.json"]
        missing_files = []
        for file_name in critical_files:
            if not (dist_assets_dir / file_name).exists():
                missing_files.append(file_name)
        
        if missing_files:
            print(f"警告: 缺少以下关键assets文件: {missing_files}")
    else:
        print("警告: uiautomator2 assets 目录不存在")
    
    # 添加adbutils的binaries目录文件（包含adb.exe等）
    adbutils_binaries_dir = PROJECT_ROOT / ".venv" / "Lib" / "site-packages" / "adbutils" / "binaries"
    if adbutils_binaries_dir.exists():
        # 复制到 dist_nuitka 目录
        dist_binaries_dir = PROJECT_ROOT / "dist_nuitka" / "adbutils" / "binaries"
        if dist_binaries_dir.exists():
            shutil.rmtree(dist_binaries_dir)
        dist_binaries_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(adbutils_binaries_dir, dist_binaries_dir)
        print(f"已复制 adbutils binaries 目录到: {dist_binaries_dir}")
        
        # 复制到 build_nuitka 目录
        build_binaries_dir = CONFIG["build_dir"] / "adbutils" / "binaries"
        if build_binaries_dir.exists():
            shutil.rmtree(build_binaries_dir)
        build_binaries_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(adbutils_binaries_dir, build_binaries_dir)
        print(f"已复制 adbutils binaries 目录到: {build_binaries_dir}")
        
        # 添加到Nuitka构建命令
        cmd.append(f"--include-package-data=adbutils")
        
        # 列出复制的文件
        binary_files = list(dist_binaries_dir.rglob("*"))
        binary_files = [f for f in binary_files if f.is_file()]
        print(f"已包含 {len(binary_files)} 个adbutils binaries文件")
        
        # 验证关键文件
        critical_binary_files = ["adb.exe", "__init__.py"]
        missing_binary_files = []
        for file_name in critical_binary_files:
            if not (dist_binaries_dir / file_name).exists():
                missing_binary_files.append(file_name)
        
        if missing_binary_files:
            print(f"警告: 缺少以下关键binaries文件: {missing_binary_files}")
    else:
        print("警告: adbutils binaries 目录不存在")
    
    # Nuitka 2.8.x 兼容性修复
    try:
        # 尝试多种方式获取 Nuitka 版本
        nuitka_version = None
        
        # 方法1: 尝试通过命令行获取版本
        try:
            result = subprocess.run(
                [sys.executable, "-m", "nuitka", "--version"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            if result.returncode == 0:
                # 解析版本号（第一行）
                version_line = result.stdout.strip().split('\n')[0]
                nuitka_version = version_line.strip()
        except (subprocess.SubprocessError, OSError):
            pass
        
        # 方法2: 尝试从模块获取版本
        if not nuitka_version:
            try:
                import nuitka
                if hasattr(nuitka, 'Version'):
                    nuitka_version = nuitka.Version.getNuitkaVersion()
                elif hasattr(nuitka, '__version__'):
                    nuitka_version = nuitka.__version__
            except (ImportError, AttributeError):
                pass
        
        if nuitka_version and nuitka_version.startswith('2.8.'):
            print(f"当前 Nuitka 版本: {nuitka_version}")
            print("应用 Nuitka 2.8.x 兼容性修复")
            cmd.extend([
                "--experimental=use_all_compatible_files",
                "--experimental=use_older_gcc",
                "--experimental=no_use_temp_directory",
            ])
        
        # 显示性能优化信息
        print(f"检测到 CPU 核心数: {os.cpu_count()}")
        print(f"已启用并行编译，使用 {os.cpu_count()} 个核心")
        print("性能优化已应用:")
        print("  - 并行编译 (--jobs)")
        print("  - LTO 链接优化 (--lto=yes)")
        print("  - 排除额外测试模块")
    except Exception as e:
        print(f"警告: 无法检测 Nuitka 版本: {e}")

    
    # 主脚本
    cmd.append(str(PROJECT_ROOT / CONFIG["main_script"]))
    
    return cmd


def build_onefile():
    """构建单文件版本"""
    print("=" * 60)
    print("开始构建Nuitka单文件版本")
    print("=" * 60)
    
    # 清理旧的构建目录
    if CONFIG["build_dir"].exists():
        shutil.rmtree(CONFIG["build_dir"])
    
    # 创建构建目录
    CONFIG["build_dir"].mkdir(parents=True, exist_ok=True)
    
    # 生成构建命令
    cmd = get_nuitka_command("onefile")
    
    print("Nuitka构建命令:")
    try:
        # 设置标准输出编码为UTF-8以避免编码错误
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        print(" ".join(cmd))
    except UnicodeEncodeError:
        # 如果仍然有编码问题，使用安全的方式打印
        safe_cmd = []
        for part in cmd:
            if isinstance(part, str):
                safe_cmd.append(part.encode('utf-8', errors='replace').decode('utf-8'))
            else:
                safe_cmd.append(str(part))
        print(" ".join(safe_cmd))
    print("-" * 60)
    
    # 执行构建
    try:
        # 不使用text=True，而是手动处理编码
        result = subprocess.run(cmd, check=True, capture_output=True)
        
        # 尝试解码输出，优先UTF-8，失败则尝试GBK
        def safe_decode(data):
            if isinstance(data, bytes):
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return data.decode('gbk')
                    except UnicodeDecodeError:
                        return data.decode('utf-8', errors='replace')
            return str(data)
        
        stdout = safe_decode(result.stdout)
        stderr = safe_decode(result.stderr)
        
        print("构建输出:")
        print(stdout)
        if stderr:
            print("构建警告/错误:")
            print(stderr)
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        # 安全处理错误输出
        error_output = ""
        if hasattr(e, 'stderr') and e.stderr:
            if isinstance(e.stderr, str):
                error_output = e.stderr
            else:
                try:
                    error_output = e.stderr.decode('utf-8', errors='replace')
                except:
                    try:
                        error_output = e.stderr.decode('gbk', errors='replace')
                    except:
                        error_output = str(e.stderr)
        print(f"错误输出: {error_output}")
        return False
    
    # 复制生成的可执行文件到dist目录
    if CONFIG["dist_dir"].exists():
        shutil.rmtree(CONFIG["dist_dir"])
    CONFIG["dist_dir"].mkdir(parents=True, exist_ok=True)
    
    # 查找生成的可执行文件
    exe_name = CONFIG["output_name"] + ".exe"
    exe_src = CONFIG["build_dir"] / exe_name
    
    if exe_src.exists():
        exe_dst = CONFIG["dist_dir"] / exe_name
        shutil.copy2(exe_src, exe_dst)
        
        # 复制其他必要文件
        for src, dst in CONFIG["data_files"]:
            src_path = PROJECT_ROOT / src
            if src_path.exists():
                dst_path = CONFIG["dist_dir"] / dst
                if dst == ".":
                    dst_path = CONFIG["dist_dir"] / src
                shutil.copy2(src_path, dst_path)
        
        # 确保uiautomator2 assets目录存在
        u2_assets_src = PROJECT_ROOT / ".venv" / "Lib" / "site-packages" / "uiautomator2" / "assets"
        u2_assets_dst = CONFIG["dist_dir"] / "uiautomator2" / "assets"
        
        if u2_assets_src.exists():
            if u2_assets_dst.exists():
                shutil.rmtree(u2_assets_dst)
            shutil.copytree(u2_assets_src, u2_assets_dst)
            print(f"已复制 uiautomator2 assets 到: {u2_assets_dst}")
        else:
            print("警告: uiautomator2 assets 目录不存在")
        
        # 确保adbutils binaries目录存在
        adbutils_binaries_src = PROJECT_ROOT / ".venv" / "Lib" / "site-packages" / "adbutils" / "binaries"
        adbutils_binaries_dst = CONFIG["dist_dir"] / "adbutils" / "binaries"
        
        if adbutils_binaries_src.exists():
            if adbutils_binaries_dst.exists():
                shutil.rmtree(adbutils_binaries_dst)
            shutil.copytree(adbutils_binaries_src, adbutils_binaries_dst)
            print(f"已复制 adbutils binaries 到: {adbutils_binaries_dst}")
        else:
            print("警告: adbutils binaries 目录不存在")
        
        print(f"\n 构建成功!")
        print(f"可执行文件: {exe_dst}")
        print(f"构建目录: {CONFIG['build_dir']}")
        print("注意: ADB工具文件将由 auto_package.py 脚本复制到 build_nuitka 目录")
        return True
    else:
        print(f" 未找到生成的可执行文件: {exe_src}")
        return False


def build_standalone():
    """构建独立目录版本"""
    print("=" * 60)
    print("开始构建Nuitka独立目录版本")
    print("=" * 60)
    
    # 清理旧的构建目录
    if CONFIG["build_dir"].exists():
        shutil.rmtree(CONFIG["build_dir"])
    
    # 创建构建目录
    CONFIG["build_dir"].mkdir(parents=True, exist_ok=True)
    
    # 生成构建命令
    cmd = get_nuitka_command("standalone")
    
    print("Nuitka构建命令:")
    print(" ".join(cmd))
    print("-" * 60)
    
    # 执行构建
    try:
        # 不使用text=True，而是手动处理编码
        result = subprocess.run(cmd, check=True, capture_output=True)
        
        # 尝试解码输出，优先UTF-8，失败则尝试GBK
        def safe_decode(data):
            if isinstance(data, bytes):
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return data.decode('gbk')
                    except UnicodeDecodeError:
                        return data.decode('utf-8', errors='replace')
            return str(data)
        
        stdout = safe_decode(result.stdout)
        stderr = safe_decode(result.stderr)
        
        print("构建输出:")
        print(stdout)
        if stderr:
            print("构建警告/错误:")
            print(stderr)
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        # 安全处理错误输出
        error_output = ""
        if hasattr(e, 'stderr') and e.stderr:
            if isinstance(e.stderr, str):
                error_output = e.stderr
            else:
                try:
                    error_output = e.stderr.decode('utf-8', errors='replace')
                except:
                    try:
                        error_output = e.stderr.decode('gbk', errors='replace')
                    except:
                        error_output = str(e.stderr)
        print(f"错误输出: {error_output}")
        return False
    
    # 查找生成的目录（Nuitka standalone 模式下目录名基于主脚本名）
    dist_dir_name = "main.dist"  # 基于 main.py
    dist_src = CONFIG["build_dir"] / dist_dir_name
    
    if not dist_src.exists():
        # 备选：尝试 output_name.dist
        dist_dir_name = CONFIG["output_name"] + ".dist"
        dist_src = CONFIG["build_dir"] / dist_dir_name
    
    if dist_src.exists():
        # 复制到最终分发目录
        if CONFIG["dist_dir"].exists():
            # 添加重试机制处理文件占用问题
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(CONFIG["dist_dir"])
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        print(f"警告: 无法删除 {CONFIG['dist_dir']} (尝试 {attempt + 1}/{max_retries})")
                        print(f"原因: {e}")
                        print("请关闭可能占用该目录的程序（如文件资源管理器、杀毒软件等）")
                        import time
                        time.sleep(2)  # 等待2秒后重试
                    else:
                        print(f"错误: 多次尝试后仍无法删除 {CONFIG['dist_dir']}")
                        print("请手动删除该目录后重新运行打包脚本")
                        return False
        
        shutil.copytree(dist_src, CONFIG["dist_dir"])
        
        # 复制其他必要文件
        for src, dst in CONFIG["data_files"]:
            src_path = PROJECT_ROOT / src
            if src_path.exists():
                if dst == ".":
                    dst_path = CONFIG["dist_dir"] / src
                else:
                    dst_path = CONFIG["dist_dir"] / dst
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
        
        print(f"\n 构建成功!")
        print(f"程序目录: {CONFIG['dist_dir']}")
        print(f"主程序: {CONFIG['dist_dir'] / CONFIG['output_name']}.exe")
        print(f"构建目录: {CONFIG['build_dir']}")
        print("注意: ADB工具文件将由 auto_package.py 脚本复制到 build_nuitka 目录")
        return True
    else:
        print(f" 未找到生成的目录: {dist_src}")
        return False


def clean_build():
    """清理构建文件"""
    print("清理构建文件...")
    
    dirs_to_clean = [
        CONFIG["build_dir"],
        CONFIG["dist_dir"],
        PROJECT_ROOT / "__pycache__",
        PROJECT_ROOT / "Function_Moudle" / "__pycache__",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  已清理: {dir_path}")
            except Exception as e:
                print(f"  清理失败 {dir_path}: {e}")
    
    # 清理.pyc文件
    for pyc_file in PROJECT_ROOT.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            print(f"  已删除: {pyc_file}")
        except Exception as e:
            print(f"  删除失败 {pyc_file}: {e}")
    
    print(" 清理完成")


def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    
    required_packages = [
        "nuitka",
        "PyQt5",
        "qdarkstyle",
        "uiautomator2",
        "adbutils",
        "openpyxl",
        "psutil",
        "lxml",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  OK {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  Error {package} (未安装)")
    
    if missing_packages:
        print(f"\n 缺少依赖包: {', '.join(missing_packages)}")
        print("请使用以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print(" 所有依赖已安装")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ADBTools Nuitka打包工具")
    parser.add_argument(
        "--build", 
        choices=["onefile", "standalone", "both"],
        help="构建类型: onefile(单文件), standalone(独立目录), both(两者都构建)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理构建文件"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查依赖"
    )
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
        return
    
    if args.check:
        check_dependencies()
        return
    
    if args.build:
        # 检查依赖
        if not check_dependencies():
            return
        
        success = True
        
        if args.build in ["onefile", "both"]:
            if not build_onefile():
                success = False
        
        if args.build in ["standalone", "both"]:
            if not build_standalone():
                success = False
        
        if success:
            print("\n" + "=" * 60)
            print("构建完成!")
            print("=" * 60)
            print(f"\n构建文件位于: {CONFIG['dist_dir']}")
            print("\n使用说明:")
            print("1. 单文件版本: 直接运行 ADBTools_nuitka.exe")
            print("2. 独立目录版本: 运行 dist_nuitka/ADBTools_nuitka.exe")
            print("\n注意: 确保ADB工具文件已正确复制到分发目录")
        else:
            print("\n 构建失败，请检查错误信息")
    else:
        parser.print_help()
        print("\n示例:")
        print("  python nuitka_build_fixed_v2.py --build onefile     # 构建单文件版本")
        print("  python nuitka_build_fixed_v2.py --build standalone  # 构建独立目录版本")
        print("  python nuitka_build_fixed_v2.py --build both        # 构建两种版本")
        print("  python nuitka_build_fixed_v2.py --clean             # 清理构建文件")
        print("  python nuitka_build_fixed_v2.py --check             # 检查依赖")


if __name__ == "__main__":
    main()