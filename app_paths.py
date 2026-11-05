#!/usr/bin/env python3
"""
应用路径工具 - 统一获取程序真实所在目录（安装目录）

背景：
Nuitka onefile 模式下 exe 是自解压程序，运行时会解压到 %TEMP%\\onefile_xxx，
此时 sys.executable / __file__ 指向临时解压目录（程序退出即被删除），
不能用于定位日志、配置等需要持久化的文件。

Nuitka 会向每个编译模块注入全局变量 __nuitka_binary_dir，
它始终指向原始 exe 所在目录（onefile 下不受解压影响），以此为准。
"""

import os
import sys


def get_app_dir() -> str:
    """获取程序真实所在目录（打包后为安装目录，开发时为项目根目录）"""
    # 1. Nuitka 注入的原始二进制目录（onefile 模式下唯一可靠的来源）
    binary_dir = globals().get("__nuitka_binary_dir")
    if binary_dir:
        return os.path.abspath(str(binary_dir))

    # 2. PyInstaller 等其他打包方式：exe 所在目录即安装目录
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))

    # 3. 开发环境：本文件所在目录（项目根目录）
    return os.path.dirname(os.path.abspath(__file__))


def is_frozen() -> bool:
    """是否为打包运行状态"""
    return bool(globals().get("__nuitka_binary_dir")) or getattr(sys, 'frozen', False)


def find_resource(filename: str) -> str:
    """查找随包分发的资源文件（UI文件等），返回第一个存在的完整路径

    搜索顺序：
    1. 运行时目录（onefile 模式下资源随包解压到临时目录）
    2. 真实安装目录（standalone 模式 / 安装器额外复制的文件）
    3. 当前工作目录（开发环境即项目根目录）
    找不到时返回安装目录下的拼接路径（由调用方报错）
    """
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.dirname(os.path.abspath(sys.executable)))
    candidates.append(get_app_dir())
    candidates.append(os.getcwd())

    for base in candidates:
        path = os.path.join(base, filename)
        if os.path.isfile(path):
            return path

    return os.path.join(get_app_dir(), filename)