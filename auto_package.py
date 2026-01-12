#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADBTools 自动打包脚本

功能：
1. 要求用户输入版本号（如：1.6.2）
2. 要求用户输入 platform-tools 文件夹路径
3. 更新配置文件中的版本号
4. 执行 python nuitka_build.py --build onefile
5. 复制 platform-tools 文件夹下所有文件到 build_nuitka 文件夹
6. 复制 adbtool.ui 和 adbtools_config.json 到 build_nuitka 文件夹
7. 通过命令行 iscc 调用编译器使用 ADBTools_setup.iss 打包成安装包

使用方法：
python auto_package.py
"""

import os
import sys
import shutil
import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 配置
CONFIG = {
    # 目标路径
    "build_dir": PROJECT_ROOT / "build_nuitka",
    "dist_dir": PROJECT_ROOT / "dist_nuitka",
    "output_dir": PROJECT_ROOT / "Output",
    
    # 需要复制的配置文件
    "config_files_to_copy": [
        "adbtool.ui",
        "adbtools_config.json",
    ],
    
    # 配置文件
    "config_file": "adbtools_config.json",
    "iss_file": "ADBTools_setup.iss",
    "icon_file": "icon.ico",
}


def get_user_inputs() -> Tuple[str, Optional[Path]]:
    """获取用户输入的版本号和platform-tools路径"""
    print("=" * 60)
    print("ADBTools 自动打包工具")
    print("=" * 60)
    
    # 获取版本号
    while True:
        version = input("请输入版本号 (格式: 主版本.次版本.修订号, 如: 1.6.2): ").strip()
        
        # 验证版本号格式
        if re.match(r'^\d+\.\d+\.\d+$', version):
            break
        else:
            print("❌ 版本号格式不正确，请使用 主版本.次版本.修订号 格式 (如: 1.6.2)")
            print("请重新输入...")
    
    # 获取platform-tools路径
    print("\n" + "-" * 60)
    print("ADB 工具文件路径设置")
    print("-" * 60)
    print("请选择 ADB 工具文件来源:")
    print("1. 手动输入 platform-tools 文件夹路径")
    print("2. 使用默认路径 (D:\\work_tools\\platform-tools)")
    print("3. 跳过 ADB 文件复制（手动复制）")
    
    while True:
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == "1":
            # 手动输入路径
            print("\n" + "-" * 60)
            print("请输入 platform-tools 文件夹路径")
            print("示例: D:\\work_tools\\platform-tools")
            print("提示: 可以直接拖拽文件夹到命令行窗口")
            print("-" * 60)
            
            while True:
                platform_tools_path = input("platform-tools 路径: ").strip()
                
                # 处理拖拽路径（可能包含引号）
                platform_tools_path = platform_tools_path.strip('"\'')
                
                path = Path(platform_tools_path)
                
                if path.exists() and path.is_dir():
                    # 检查是否包含ADB工具文件
                    adb_files = ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"]
                    missing_files = []
                    
                    for file in adb_files:
                        if not (path / file).exists():
                            missing_files.append(file)
                    
                    if missing_files:
                        print(f"⚠  警告: 未找到以下ADB工具文件: {', '.join(missing_files)}")
                        confirm = input("是否继续? (y/n): ").strip().lower()
                        if confirm in ['y', 'yes', '是']:
                            return version, path
                        else:
                            print("请重新输入路径...")
                    else:
                        print(f"✅ 找到ADB工具文件: {', '.join(adb_files)}")
                        return version, path
                else:
                    print(f"❌ 路径不存在或不是文件夹: {platform_tools_path}")
                    print("请重新输入...")
        
        elif choice == "2":
            # 使用默认路径
            default_path = Path(r"D:\work_tools\platform-tools")
            print(f"\n使用默认路径: {default_path}")
            
            if default_path.exists() and default_path.is_dir():
                # 检查是否包含ADB工具文件
                adb_files = ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"]
                missing_files = []
                
                for file in adb_files:
                    if not (default_path / file).exists():
                        missing_files.append(file)
                
                if missing_files:
                    print(f"⚠  警告: 未找到以下ADB工具文件: {', '.join(missing_files)}")
                    confirm = input("是否继续? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes', '是']:
                        return version, default_path
                    else:
                        print("请重新选择...")
                else:
                    print(f"✅ 找到ADB工具文件: {', '.join(adb_files)}")
                    return version, default_path
            else:
                print(f"❌ 默认路径不存在: {default_path}")
                print("请重新选择...")
        
        elif choice == "3":
            # 跳过ADB文件复制
            print("\n⚠  注意: 将跳过 ADB 工具文件复制")
            print("打包完成后，请手动将 ADB 工具文件复制到 build_nuitka 目录")
            print("必需的 ADB 文件: adb.exe, AdbWinApi.dll, AdbWinUsbApi.dll")
            confirm = input("确认跳过? (y/n): ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                return version, None
            else:
                print("请重新选择...")
        
        else:
            print("❌ 无效选择，请输入 1、2 或 3")


def update_config_version(version: str) -> bool:
    """更新配置文件中的版本号"""
    print(f"\n更新配置文件版本号为: {version}")
    
    try:
        # 解析版本号
        parts = version.split('.')
        if len(parts) != 3:
            print(f"❌ 版本号格式错误: {version}")
            return False
        
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        
        # 更新 config_manager.py 中的版本号
        config_manager_path = PROJECT_ROOT / "config_manager.py"
        if not config_manager_path.exists():
            print(f"❌ 配置文件不存在: {config_manager_path}")
            return False
        
        # 读取文件内容
        with open(config_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新默认配置中的版本号
        # 查找 DEFAULT_CONFIG 中的 version 部分
        pattern = r'"version":\s*\{[^}]*\}'
        new_version_config = f'''"version": {{
            "major": {major},
            "minor": {minor},
            "patch": {patch},
            "build": 0,
        }}'''
        
        # 替换版本配置
        new_content = re.sub(pattern, new_version_config, content, flags=re.DOTALL)
        
        # 写回文件
        with open(config_manager_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已更新 config_manager.py 中的版本号为: {version}")
        
        # 更新 ADBTools_setup.iss 中的版本号
        iss_path = PROJECT_ROOT / CONFIG["iss_file"]
        if iss_path.exists():
            with open(iss_path, 'r', encoding='utf-8') as f:
                iss_content = f.read()
            
            # 更新版本号定义
            iss_content = re.sub(
                r'#define MyAppVersion "[\d\.]+"',
                f'#define MyAppVersion "{version}"',
                iss_content
            )
            
            with open(iss_path, 'w', encoding='utf-8') as f:
                f.write(iss_content)
            
            print(f"✅ 已更新 {CONFIG['iss_file']} 中的版本号为: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新版本号失败: {e}")
        return False


def run_nuitka_build() -> bool:
    """执行 Nuitka 构建"""
    print("\n" + "=" * 60)
    print("开始执行 Nuitka 构建...")
    print("=" * 60)
    
    cmd = [sys.executable, "nuitka_build.py", "--build", "onefile"]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        print("构建输出:")
        print(result.stdout)
        
        if result.stderr:
            print("构建警告/错误:")
            print(result.stderr)
        
        # 检查构建是否成功
        if "构建成功" in result.stdout or "✅" in result.stdout:
            print("✅ Nuitka 构建成功")
            return True
        else:
            print("❌ Nuitka 构建可能失败，请检查输出")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 执行构建时发生错误: {e}")
        return False


def copy_files_to_build_dir(platform_tools_path: Optional[Path]) -> bool:
    """复制所有必要文件到 build_nuitka 目录"""
    print("\n" + "=" * 60)
    print("复制文件到 build_nuitka 目录...")
    print("=" * 60)
    
    build_dir = CONFIG["build_dir"]
    
    if not build_dir.exists():
        print(f"❌ build_nuitka 文件夹不存在: {build_dir}")
        print("请先运行 Nuitka 构建")
        return False
    
    total_copied = 0
    
    # 1. 复制 platform-tools 文件（如果提供了路径）
    if platform_tools_path is not None:
        print("1. 复制 platform-tools 文件:")
        if platform_tools_path.exists() and platform_tools_path.is_dir():
            platform_files_copied = 0
            try:
                for item in platform_tools_path.iterdir():
                    if item.is_file():
                        dest_path = build_dir / item.name
                        shutil.copy2(item, dest_path)
                        print(f"   ✓ {item.name}")
                        platform_files_copied += 1
                
                print(f"   ✅ 已复制 {platform_files_copied} 个 platform-tools 文件")
                total_copied += platform_files_copied
            except Exception as e:
                print(f"   ❌ 复制 platform-tools 文件失败: {e}")
        else:
            print(f"   ❌ platform-tools 文件夹不存在: {platform_tools_path}")
    else:
        print("1. 跳过 platform-tools 文件复制")
        print("   ⚠  用户选择跳过 ADB 工具文件复制")
        print("   打包完成后，请手动将以下文件复制到 build_nuitka 目录:")
        print("   - adb.exe")
        print("   - AdbWinApi.dll")
        print("   - AdbWinUsbApi.dll")
    
    # 2. 复制配置文件
    print("\n2. 复制配置文件:")
    config_files_copied = 0
    for filename in CONFIG["config_files_to_copy"]:
        src_path = PROJECT_ROOT / filename
        if src_path.exists():
            dest_path = build_dir / filename
            shutil.copy2(src_path, dest_path)
            print(f"   ✓ {filename}")
            config_files_copied += 1
        else:
            print(f"   ⚠  文件不存在: {filename}")
    
    print(f"   ✅ 已复制 {config_files_copied} 个配置文件")
    total_copied += config_files_copied
    
    # 3. 复制图标文件（如果存在）
    icon_src = PROJECT_ROOT / CONFIG["icon_file"]
    if icon_src.exists():
        icon_dest = build_dir / CONFIG["icon_file"]
        shutil.copy2(icon_src, icon_dest)
        print(f"\n3. 复制图标文件:")
        print(f"   ✓ {CONFIG['icon_file']}")
        total_copied += 1
    
    print(f"\n✅ 总共复制了 {total_copied} 个文件到 {build_dir}")
    return total_copied > 0





def run_inno_setup() -> bool:
    """运行 Inno Setup 编译器"""
    print("\n" + "=" * 60)
    print("运行 Inno Setup 编译器...")
    print("=" * 60)
    
    iss_path = PROJECT_ROOT / CONFIG["iss_file"]
    
    if not iss_path.exists():
        print(f"❌ Inno Setup 脚本不存在: {iss_path}")
        return False
    
    # 检查 iscc 是否在 PATH 中
    try:
        # 尝试运行 iscc --help 来检查是否可用
        subprocess.run(["iscc", "--help"], capture_output=True, check=True)
        iscc_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        iscc_available = False
    
    if not iscc_available:
        print("⚠  iscc 命令未找到，请确保 Inno Setup 已安装并添加到 PATH")
        print("常见安装路径:")
        print("  - C:\\Program Files (x86)\\Inno Setup 6\\iscc.exe")
        print("  - C:\\Program Files\\Inno Setup 6\\iscc.exe")
        
        # 尝试常见路径
        common_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\iscc.exe",
            r"C:\Program Files\Inno Setup 6\iscc.exe",
        ]
        
        iscc_path = None
        for path in common_paths:
            if Path(path).exists():
                iscc_path = path
                break
        
        if not iscc_path:
            print("❌ 未找到 iscc.exe，请手动安装 Inno Setup")
            return False
    else:
        iscc_path = "iscc"
    
    # 确保输出目录存在
    output_dir = CONFIG["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 构建命令
    cmd = [iscc_path, str(iss_path)]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        print("Inno Setup 输出:")
        print(result.stdout)
        
        if result.stderr:
            print("Inno Setup 警告/错误:")
            print(result.stderr)
        
        # 检查是否成功生成安装包
        setup_exe = output_dir / "ADBTools_Setup.exe"
        if setup_exe.exists():
            print(f"✅ Inno Setup 打包成功")
            print(f"安装包位置: {setup_exe}")
            print(f"安装包大小: {setup_exe.stat().st_size / (1024*1024):.2f} MB")
            return True
        else:
            print("❌ 未找到生成的安装包")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Inno Setup 编译失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 执行 Inno Setup 时发生错误: {e}")
        return False


def verify_build_files(platform_tools_path: Optional[Path]) -> bool:
    """验证构建文件是否完整"""
    print("\n" + "=" * 60)
    print("验证构建文件...")
    print("=" * 60)
    
    build_dir = CONFIG["build_dir"]
    
    if not build_dir.exists():
        print(f"❌ build_nuitka 文件夹不存在")
        return False
    
    # 基础关键文件（无论是否复制ADB文件都需要）
    base_critical_files = [
        "ADBTools_nuitka.exe",
        "adbtool.ui",
        "adbtools_config.json",
    ]
    
    # ADB关键文件（只有在复制了ADB文件时才需要检查）
    adb_critical_files = [
        "adb.exe",
        "AdbWinApi.dll",
        "AdbWinUsbApi.dll",
    ]
    
    # 根据是否复制了ADB文件来确定需要检查的文件列表
    if platform_tools_path is not None:
        critical_files = base_critical_files + adb_critical_files
        print("检查所有关键文件（包括ADB工具文件）:")
    else:
        critical_files = base_critical_files
        print("检查基础关键文件（跳过ADB工具文件检查）:")
        print("⚠  注意：ADB工具文件需要手动复制到 build_nuitka 目录")
    
    missing_files = []
    for filename in critical_files:
        file_path = build_dir / filename
        if file_path.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ❌ {filename} (缺失)")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n❌ 缺失 {len(missing_files)} 个关键文件: {', '.join(missing_files)}")
        
        # 提供修复建议
        if platform_tools_path is None and any(f in missing_files for f in adb_critical_files):
            print("\n修复建议:")
            print("1. 手动复制以下ADB工具文件到 build_nuitka 目录:")
            for file in adb_critical_files:
                if file in missing_files:
                    print(f"   - {file}")
            print("2. 重新运行验证")
        
        return False
    
    print("\n✅ 所有关键文件都存在")
    return True


def cleanup_temp_files() -> None:
    """清理临时文件（可选）"""
    print("\n" + "=" * 60)
    print("清理临时文件...")
    print("=" * 60)
    
    # 可以清理的临时目录/文件
    temp_dirs = [
        PROJECT_ROOT / "__pycache__",
        PROJECT_ROOT / "Function_Moudle" / "__pycache__",
    ]
    
    for temp_dir in temp_dirs:
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                print(f"  ✓ 已清理: {temp_dir.name}")
            except Exception as e:
                print(f"  ⚠ 清理失败 {temp_dir.name}: {e}")
    
    print("✅ 临时文件清理完成")


def main():
    """主函数"""
    try:
        # 1. 获取用户输入的版本号和platform-tools路径
        version, platform_tools_path = get_user_inputs()
        
        # 确认继续
        print(f"\n" + "=" * 60)
        print(f"打包配置确认:")
        print(f"版本号: {version}")
        print(f"platform-tools 路径: {platform_tools_path}")
        print("=" * 60)
        
        confirm = input("\n是否开始打包? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("打包已取消")
            return
        
        # 2. 更新配置文件中的版本号
        if not update_config_version(version):
            print("❌ 版本号更新失败，打包中止")
            return
        
        # 3. 执行 Nuitka 构建
        if not run_nuitka_build():
            print("❌ Nuitka 构建失败，打包中止")
            return
        
        # 4. 复制所有必要文件到 build_nuitka
        if not copy_files_to_build_dir(platform_tools_path):
            print("⚠ 文件复制过程中出现问题，继续打包...")
        
        # 5. 验证构建文件
        if not verify_build_files(platform_tools_path):
            print("❌ 构建文件验证失败，打包中止")
            return
        
        # 6. 运行 Inno Setup 编译器
        if not run_inno_setup():
            print("❌ Inno Setup 打包失败")
            return
        
        # 7. 清理临时文件（可选）
        cleanup_choice = input("\n是否清理临时文件? (y/n): ").strip().lower()
        if cleanup_choice in ['y', 'yes', '是']:
            cleanup_temp_files()
        
        print("\n" + "=" * 60)
        print("✅ 自动打包完成!")
        print("=" * 60)
        print(f"\n版本号: {version}")
        print(f"platform-tools 路径: {platform_tools_path}")
        print(f"安装包位置: {CONFIG['output_dir']}\\ADBTools_Setup.exe")
        print(f"构建目录: {CONFIG['build_dir']}")
        print(f"分发目录: {CONFIG['dist_dir']}")
        print("\n打包流程总结:")
        print("1. ✓ 版本号更新")
        print("2. ✓ Nuitka 构建")
        print("3. ✓ 文件复制 (platform-tools + 配置文件)")
        print("4. ✓ Inno Setup 打包")
        print("\n可以开始分发安装包了!")
        
    except KeyboardInterrupt:
        print("\n\n❌ 打包被用户中断")
    except Exception as e:
        print(f"\n❌ 打包过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()