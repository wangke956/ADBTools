#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成Inno Setup脚本
从config_manager读取版本号，动态生成ISS文件
"""

import os
import sys
from pathlib import Path

def generate_iss_file():
    """生成Inno Setup脚本文件"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.absolute()
    
    # 从config_manager获取版本号
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from config_manager import config_manager
        version = config_manager.get_version()
        print(f"从config_manager获取版本号: {version}")
    except ImportError as e:
        print(f"无法导入config_manager: {e}")
        version = "1.5.0"
        print(f"使用默认版本号: {version}")
    except Exception as e:
        print(f"获取版本号失败: {e}")
        version = "1.5.0"
        print(f"使用默认版本号: {version}")
    
    # 读取现有的ISS文件模板
    template_file = PROJECT_ROOT / "ADBTools_setup.iss"
    if not template_file.exists():
        print(f"错误: ISS模板文件不存在: {template_file}")
        return None
    
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 替换版本号
    # 查找 #define MyAppVersion 行并替换版本号
    lines = template_content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('#define MyAppVersion'):
            # 找到版本号定义行
            lines[i] = f'#define MyAppVersion "{version}"'
            print(f"已更新版本号: {lines[i]}")
            break
    
    # 重新组合内容
    new_content = '\n'.join(lines)
    
    # 写入新的ISS文件（覆盖原文件）
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 已更新ISS文件: {template_file}")
    print(f"   版本号: {version}")
    
    return template_file

if __name__ == "__main__":
    generate_iss_file()