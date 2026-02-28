#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADBTools 自动发布脚本（版本2）

功能：
1. 从 auto_package.py 配置中读取版本号
2. 执行完整打包流程
3. 创建 Git 标签
4. 使用 gh 命令发布版本到 GitHub

使用方法：
python release_v2_fixed.py
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
        import re
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

def check_existing_build() -> bool:
    """检查已有的构建文件"""
    print("\n" + "=" * 60)
    print("检查已有的构建文件...")
    print("=" * 60)
    
    # 检查 dist_nuitka 目录
    dist_dir = PROJECT_ROOT / "dist_nuitka"
    if not dist_dir.exists():
        print(f"❌ dist_nuitka 目录不存在: {dist_dir}")
        return False
    
    # 检查可执行文件
    exe_file = dist_dir / "ADBTools_nuitka.exe"
    if not exe_file.exists():
        print(f"❌ 可执行文件不存在: {exe_file}")
        return False
    
    # 检查配置文件
    config_files = ["adbtool.ui", "adbtools_config.json"]
    for filename in config_files:
        file_path = dist_dir / filename
        if not file_path.exists():
            print(f"❌ 配置文件不存在: {file_path}")
            return False
    
    print(f"✅ dist_nuitka 目录检查通过")
    print(f"   可执行文件: {exe_file}")
    print(f"   大小: {exe_file.stat().st_size / (1024*1024):.2f} MB")
    
    # 检查 Output 目录中的安装包
    output_dir = PROJECT_ROOT / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    setup_exe = output_dir / "ADBTools_Setup.exe"
    if setup_exe.exists():
        print(f"✅ 安装包已存在: {setup_exe}")
        print(f"   大小: {setup_exe.stat().st_size / (1024*1024):.2f} MB")
    else:
        print(f"⚠ 安装包不存在: {setup_exe}")
        print("   将跳过 Inno Setup 步骤")
    
    return True

def copy_dist_to_build_dir() -> bool:
    """复制 dist_nuitka 文件到 build_nuitka"""
    print("\n" + "=" * 60)
    print("复制 dist_nuitka 文件到 build_nuitka...")
    print("=" * 60)
    
    dist_dir = PROJECT_ROOT / "dist_nuitka"
    build_dir = PROJECT_ROOT / "build_nuitka"
    
    if not dist_dir.exists():
        print(f"❌ dist_nuitka 文件夹不存在: {dist_dir}")
        return False
    
    # 删除旧的 build_nuitka
    import shutil
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # 复制整个 dist_nuitka 目录到 build_nuitka
    try:
        shutil.copytree(dist_dir, build_dir)
        print(f"✅ 已复制 {dist_dir} -> {build_dir}")
        return True
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        return False

def run_inno_setup_if_needed() -> bool:
    """如果需要，运行 Inno Setup 编译器"""
    print("\n" + "=" * 60)
    print("检查是否需要生成安装包...")
    print("=" * 60)
    
    output_dir = PROJECT_ROOT / "Output"
    setup_exe = output_dir / "ADBTools_Setup.exe"
    
    if setup_exe.exists():
        print(f"✅ 安装包已存在，跳过 Inno Setup")
        return True
    
    print("⚠ 安装包不存在，需要生成...")
    
    # 检查 ISS 文件
    iss_path = PROJECT_ROOT / "ADBTools_setup.iss"
    if not iss_path.exists():
        print(f"❌ Inno Setup 脚本不存在: {iss_path}")
        return False
    
    # 检查 iscc 命令
    try:
        subprocess.run(["iscc", "--help"], capture_output=True, check=True)
        iscc_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        iscc_available = False
    
    if not iscc_available:
        print("⚠  iscc 命令未找到，尝试常见路径...")
        common_paths = [
            r"C:\\Program Files (x86)\\Inno Setup 6\\iscc.exe",
            r"C:\\Program Files\\Inno Setup 6\\iscc.exe",
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
    
    cmd = [iscc_path, str(iss_path)]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        print(result.stdout)
        
        if setup_exe.exists():
            print(f"✅ 安装包生成成功: {setup_exe}")
            print(f"大小: {setup_exe.stat().st_size / (1024*1024):.2f} MB")
            return True
        else:
            print("❌ 未找到生成的安装包")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Inno Setup 编译失败: {e}")
        print(e.stderr)
        return False

def commit_and_tag(version: str) -> bool:
    """提交更改并创建标签"""
    print("\n" + "=" * 60)
    print("提交更改并创建标签...")
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
    
    # 2. 添加文件到 git
    print("添加文件到 git...")
    try:
        subprocess.run(["git", "add", "."], check=True, cwd=PROJECT_ROOT)
        print("✅ 文件已添加")
    except subprocess.CalledProcessError as e:
        print(f"❌ 添加文件失败: {e}")
        return False
    
    # 3. 提交更改
    commit_msg = f"Release v{version}"
    print(f"提交更改: {commit_msg}")
    try:
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=PROJECT_ROOT)
        print("✅ 提交成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 提交失败: {e}")
        return False
    
    # 4. 创建标签
    tag_name = f"v{version}"
    print(f"创建标签: {tag_name}")
    try:
        subprocess.run(["git", "tag", tag_name], check=True, cwd=PROJECT_ROOT)
        print(f"✅ 标签 {tag_name} 创建成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建标签失败: {e}")
        return False
    
    return True

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
        print(f"⚠ 安装包不存在: {setup_exe}")
        print("将创建无附件的发布")
        assets = []
    else:
        assets = [str(setup_exe)]
    
    # 构建 gh release 命令
    cmd = ["gh", "release", "create", tag_name, "--title", release_name]
    
    if assets:
        for asset in assets:
            cmd.extend(["--asset", asset])
    
    # 添加发布描述
    description = f"""
## ADBTools v{version}

ADB 工具 GUI 版本，用于 Android 开发和调试。

### 主要功能
- ADB 命令执行
- 应用管理
- 设备信息查看
- 批量操作支持

### 安装
下载并运行 `ADBTools_Setup.exe` 安装程序。

### 仓库
{repo_url}

### 更新日志
请查看 [Release Notes](https://github.com/wangke956/ADBTools/releases)

---
ADBTools - Android Debug Bridge GUI Tool
"""
    
    # 临时创建描述文件
    desc_file = PROJECT_ROOT / "release_description.txt"
    with open(desc_file, 'w', encoding='utf-8') as f:
        f.write(description)
    
    cmd.extend(["--notes-file", str(desc_file)])
    
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
        # 2. 检查已有的构建文件
        if not check_existing_build():
            print("❌ 构建文件检查失败")
            return
        
        # 3. 复制 dist_nuitka 文件到 build_nuitka
        if not copy_dist_to_build_dir():
            print("❌ 文件复制失败")
            return
        
        # 4. 运行 Inno Setup（如果需要）
        if not run_inno_setup_if_needed():
            print("❌ Inno Setup 打包失败")
            return
        
        # 5. 提交并创建标签
        if not commit_and_tag(version):
            print("❌ 提交或创建标签失败")
            return
        
        # 6. 创建 GitHub 发布
        if not create_github_release(version):
            print("❌ 创建 GitHub 发布失败")
            return
        
        # 7. 推送到远程仓库
        print("\n" + "=" * 60)
        print("推送到远程仓库...")
        print("=" * 60)
        
        tag_name = f"v{version}"
        try:
            subprocess.run(["git", "push", "origin", tag_name], check=True, cwd=PROJECT_ROOT)
            print(f"✅ 标签已推送到远程仓库")
        except subprocess.CalledProcessError as e:
            print(f"⚠ 推送标签失败: {e}")
            print("请手动推送标签: git push origin " + tag_name)
        
        try:
            subprocess.run(["git", "push", "origin", "HEAD"], check=True, cwd=PROJECT_ROOT)
            print("✅ 代码已推送到远程仓库")
        except subprocess.CalledProcessError as e:
            print(f"⚠ 推送代码失败: {e}")
            print("请手动推送: git push origin HEAD")
        
        # 8. 完成
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