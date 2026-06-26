#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 专用构建脚本

简化版本，适用于 CI/CD 环境
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """执行命令并输出结果"""
    if description:
        print(f"\n{'='*60}")
        print(f"📌 {description}")
        print(f"{'='*60}")
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败 (退出码: {e.returncode})")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """主函数"""
    print("🚀 ADBTools GitHub Actions 构建脚本")
    print(f"Python 版本: {sys.version}")
    print(f"工作目录: {Path.cwd()}")
    
    # 检查必要文件
    required_files = [
        "main.py",
        "nuitka_build_fixed_v2.py",
        "requirements_nuitka.txt",
    ]
    
    print("\n📋 检查必要文件...")
    for file in required_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} 不存在!")
            return False
    
    # 安装依赖（如果需要）
    print("\n📦 检查依赖...")
    try:
        import nuitka
        import PyQt5
        import uiautomator2
        import adbutils
        print("  ✅ 所有依赖已安装")
    except ImportError as e:
        print(f"  ⚠️  缺少依赖: {e}")
        print("  正在安装依赖...")
        if not run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements_nuitka.txt"],
            "安装 Python 依赖"
        ):
            return False
    
    # 执行构建
    print("\n🔨 开始 Nuitka 构建...")
    if not run_command(
        [sys.executable, "nuitka_build_fixed_v2.py", "--build", "onefile"],
        "Nuitka OneFile 构建"
    ):
        return False
    
    # 验证输出
    print("\n✅ 验证构建结果...")
    exe_path = Path("dist_nuitka/ADBTools_nuitka.exe")
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ 可执行文件生成成功!")
        print(f"  📍 路径: {exe_path.absolute()}")
        print(f"  📏 大小: {size_mb:.2f} MB")
        return True
    else:
        print(f"  ❌ 未找到可执行文件: {exe_path}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
