#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuitka打包配置文件
用于将ADBTools打包为独立的可执行文件

使用方法:
python nuitka_build.py --build  # 构建可执行文件
python nuitka_build.py --clean  # 清理构建文件
python nuitka_build.py --help   # 显示帮助信息
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
    
    # 需要排除的模块（减小体积）
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
        # 只复制关键的assets文件，忽略.gitignore等非必要文件
        critical_assets = ["u2.jar", "app-uiautomator.apk", "version.json", "sync.sh"]
        copied_count = 0
        
        for asset_name in critical_assets:
            asset_file = u2_assets_dir / asset_name
            if asset_file.exists() and asset_file.is_file():
                # 保持目录结构：uiautomator2/assets/文件名
                cmd.append(f"--include-data-files={asset_file}=uiautomator2/assets/{asset_name}")
                copied_count += 1
        
        print(f"已包含 {copied_count} 个uiautomator2关键assets文件")
        if copied_count < len(critical_assets):
            missing = [a for a in critical_assets if not (u2_assets_dir / a).exists()]
            print(f"警告: 缺少以下assets文件: {missing}")
    
    # 主脚本
    cmd.append(str(PROJECT_ROOT / CONFIG["main_script"]))
    
    return cmd


def copy_adb_tools(dist_path):
    """复制ADB工具文件到分发目录"""
    print("复制ADB工具文件...")
    
    adb_files = [
        ("adb.exe", "ADB工具主程序"),
        ("AdbWinApi.dll", "ADB API DLL"),
        ("AdbWinUsbApi.dll", "ADB USB DLL"),
        ("aapt.exe", "Android Asset Packaging Tool"),
        ("fastboot.exe", "Fastboot工具"),
        ("hprof-conv.exe", "Heap Profile转换工具"),
        ("sqlite3.exe", "SQLite3数据库工具"),
        ("etc1tool.exe", "ETC1纹理工具"),
        ("make_f2fs.exe", "F2FS文件系统工具"),
        ("make_f2fs_casefold.exe", "F2FS Casefold工具"),
        ("mke2fs.exe", "Ext2/3/4文件系统工具"),
        ("mke2fs.conf", "Ext文件系统配置"),
        ("libwinpthread-1.dll", "Windows线程库"),
        ("source.properties", "ADB源属性文件"),
        ("NOTICE.txt", "许可证声明"),
    ]
    
    copied_count = 0
    for filename, description in adb_files:
        src = PROJECT_ROOT / filename
        if src.exists():
            dst = dist_path / filename
            shutil.copy2(src, dst)
            print(f"  ✓ {filename} ({description})")
            copied_count += 1
        else:
            # 检查dist目录中是否已有
            dist_src = PROJECT_ROOT / "dist" / filename
            if dist_src.exists():
                dst = dist_path / filename
                shutil.copy2(dist_src, dst)
                print(f"  ✓ {filename} (从dist目录复制)")
                copied_count += 1
    
    print(f"已复制 {copied_count} 个ADB工具文件")


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
    print(" ".join(cmd))
    print("-" * 60)
    
    # 执行构建
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建输出:")
        print(result.stdout)
        if result.stderr:
            print("构建警告/错误:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
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
        
        # 复制ADB工具文件
        copy_adb_tools(CONFIG["dist_dir"])
        
        # 复制其他必要文件
        for src, dst in CONFIG["data_files"]:
            src_path = PROJECT_ROOT / src
            if src_path.exists():
                dst_path = CONFIG["dist_dir"] / dst
                if dst == ".":
                    dst_path = CONFIG["dist_dir"] / src
                shutil.copy2(src_path, dst_path)
        
        print(f"\n✅ 构建成功!")
        print(f"可执行文件: {exe_dst}")
        print(f"构建目录: {CONFIG['build_dir']}")
        print(f"分发目录: {CONFIG['dist_dir']}")
        return True
    else:
        print(f"❌ 未找到生成的可执行文件: {exe_src}")
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
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建输出:")
        print(result.stdout)
        if result.stderr:
            print("构建警告/错误:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    
    # 查找生成的目录
    dist_dir_name = CONFIG["output_name"] + ".dist"
    dist_src = CONFIG["build_dir"] / dist_dir_name
    
    if dist_src.exists():
        # 复制到最终分发目录
        if CONFIG["dist_dir"].exists():
            shutil.rmtree(CONFIG["dist_dir"])
        
        shutil.copytree(dist_src, CONFIG["dist_dir"])
        
        # 复制ADB工具文件
        copy_adb_tools(CONFIG["dist_dir"])
        
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
        
        print(f"\n✅ 构建成功!")
        print(f"程序目录: {CONFIG['dist_dir']}")
        print(f"主程序: {CONFIG['dist_dir'] / CONFIG['output_name']}.exe")
        print(f"构建目录: {CONFIG['build_dir']}")
        return True
    else:
        print(f"❌ 未找到生成的目录: {dist_src}")
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
    
    print("✅ 清理完成")


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
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ✗ {package} (未安装)")
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请使用以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖已安装")
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
            print("\n❌ 构建失败，请检查错误信息")
    else:
        parser.print_help()
        print("\n示例:")
        print("  python nuitka_build.py --build onefile     # 构建单文件版本")
        print("  python nuitka_build.py --build standalone  # 构建独立目录版本")
        print("  python nuitka_build.py --build both        # 构建两种版本")
        print("  python nuitka_build.py --clean             # 清理构建文件")
        print("  python nuitka_build.py --check             # 检查依赖")


if __name__ == "__main__":
    main()