#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADBTools 最简单发布脚本

功能：
1. 从 auto_package.py 配置中读取版本号
2. 推送 Output 目录中的安装包到 GitHub 发布

使用方法：
python release_simplest.py
"""

import os
import sys
import subprocess
import re
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

def get_version_from_auto_package() -> str:
    """从 auto_package.py 配置中读取版本号"""
    print("从 auto_package.py 配置中读取版本号...")
    
    try:
        # 读取 config_manager.py 获取版本号
        config_manager_path = PROJECT_ROOT / "config_manager.py"
        with open(config_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找版本号
        pattern = r'"major":\s*(\d+),\s*"minor":\s*(\d+),\s*"patch":\s*(\d+)'
        match = re.search(pattern, content)
        
        if match:
            major, minor, patch = match.groups()
            version = f"{major}.{minor}.{patch}"
            print(f"✅ 从 config_manager.py 读取到版本号: {version}")
            return version
        
        # 如果没找到，尝试从 adbtools_config.json 读取
        config_file_path = PROJECT_ROOT / "adbtools_config.json"
        if config_file_path.exists():
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if 'version' in config_data:
                version = f"{config_data['version']['major']}.{config_data['version']['minor']}.{config_data['version']['patch']}"
                print(f"✅ 从 adbtools_config.json 读取到版本号: {version}")
                return version
        
        print("❌ 未找到版本号配置")
        return None
        
    except Exception as e:
        print(f"❌ 读取版本号失败: {e}")
        return None

def create_github_release(version: str) -> bool:
    """创建 GitHub 发布"""
    print("\n" + "=" * 60)
    print("创建 GitHub 发布...")
    print("=" * 60)
    
    # 1. 检查 gh 命令
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
        gh_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        gh_available = False
    
    if not gh_available:
        print("❌ gh 命令未找到，请安装 GitHub CLI")
        print("下载地址: https://cli.github.com/")
        return False
    
    # 2. 获取项目信息
    try:
        repo_info = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        repo_url = repo_info.stdout.strip()
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        print(f"仓库地址: {repo_url}")
    except subprocess.CalledProcessError:
        print("⚠ 无法获取仓库地址")
        repo_url = ""
    
    # 3. 创建发布
    tag_name = f"v{version}"
    release_name = f"ADBTools v{version}"
    
    # 检查安装包是否存在
    setup_exe = PROJECT_ROOT / "Output" / "ADBTools_Setup.exe"
    if not setup_exe.exists():
        print(f"❌ 安装包不存在: {setup_exe}")
        return False
    
    # 构建 gh release 命令
    cmd = ["gh", "release", "create", tag_name, "--title", release_name]
    
    # 添加发布描述
    description = f"""
## ADBTools v{version}
"""
    
    # 临时创建描述文件
    desc_file = PROJECT_ROOT / "release_description.txt"
    with open(desc_file, 'w', encoding='utf-8') as f:
        f.write(description)
    
    cmd.extend(["--notes-file", str(desc_file)])
    
    # 添加附件
    cmd.append(str(setup_exe))
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        print(result.stdout)
        print("✅ GitHub 发布创建成功")
        
        # 清理临时文件
        desc_file.unlink(missing_ok=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建 GitHub 发布失败: {e}")
        print(e.stderr)
        
        # 清理临时文件
        desc_file.unlink(missing_ok=True)
        
        return False

def main():
    """主函数"""
    # 1. 从 auto_package.py 配置中读取版本号
    version = get_version_from_auto_package()
    if not version:
        print("❌ 无法从配置文件读取版本号")
        print("请先运行 auto_package.py 设置版本号")
        return
    
    print(f"\n开始发布版本: {version}")
    
    try:
        # 2. 推送标签到远程仓库
        print("\n" + "=" * 60)
        print("推送标签到远程仓库...")
        print("=" * 60)
        
        tag_name = f"v{version}"
        try:
            subprocess.run(["git", "push", "origin", tag_name], check=True, cwd=PROJECT_ROOT)
            print(f"✅ 标签已推送到远程仓库")
        except subprocess.CalledProcessError as e:
            print(f"⚠ 推送标签失败: {e}")
            print("请手动推送标签: git push origin " + tag_name)
        
        # 3. 创建 GitHub 发布
        if not create_github_release(version):
            print("❌ 创建 GitHub 发布失败")
            return
        
        # 4. 完成
        print("\n" + "=" * 60)
        print("✅ 发布完成!")
        print("=" * 60)
        print(f"\n版本号: {version}")
        print(f"安装包位置: Output/ADBTools_Setup.exe")
        print(f"GitHub 发布: https://github.com/wangke956/ADBTools/releases/tag/v{version}")
        
    except KeyboardInterrupt:
        print("\n\n❌ 发布被用户中断")
    except Exception as e:
        print(f"\n❌ 发布过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
