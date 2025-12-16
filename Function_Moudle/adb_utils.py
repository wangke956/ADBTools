"""
ADB工具函数模块
提供通用的ADB操作功能
"""

import subprocess
import re


def safe_subprocess_run(command, shell=True, **kwargs):
    """
    安全的subprocess.run调用，自动处理编码问题
    
    Args:
        command (str): 要执行的命令
        shell (bool): 是否使用shell
        **kwargs: 其他subprocess.run参数
        
    Returns:
        subprocess.CompletedProcess: 执行结果
    """
    # 设置默认的编码处理参数
    default_kwargs = {
        'encoding': 'utf-8',
        'errors': 'ignore'
    }
    default_kwargs.update(kwargs)
    
    try:
        return subprocess.run(command, shell=shell, **default_kwargs)
    except UnicodeDecodeError:
        # 如果仍然出现编码错误，使用更安全的方式
        kwargs['encoding'] = 'utf-8'
        kwargs['errors'] = 'replace'
        return subprocess.run(command, shell=shell, **kwargs)


def check_device_connection(device_id):
    """
    检查设备连接状态
    
    Args:
        device_id (str): 设备ID
        
    Returns:
        tuple: (is_connected, error_message)
    """
    try:
        check_command = f"adb -s {device_id} shell echo 'connection_test'"
        check_result = safe_subprocess_run(check_command, capture_output=True, text=True, timeout=10)
        
        if check_result.returncode != 0:
            error_msg = check_result.stderr.lower()
            if "device not found" in error_msg:
                return False, f"设备 {device_id} 未连接，请检查设备连接状态"
            elif "offline" in error_msg:
                return False, f"设备 {device_id} 处于离线状态，请重新连接"
            elif "no devices" in error_msg:
                return False, "未找到任何设备，请确保设备已连接"
            else:
                return False, f"ADB连接失败: {check_result.stderr}"
        
        return True, "连接正常"
        
    except subprocess.TimeoutExpired:
        return False, "连接超时，请检查网络连接"
    except Exception as e:
        return False, f"设备连接检查失败: {str(e)}"


def get_foreground_app_info(device_id):
    """
    获取前台应用信息
    
    Args:
        device_id (str): 设备ID
        
    Returns:
        tuple: (success, result_info)
    """
    try:
        # 首先检查设备连接
        is_connected, error_msg = check_device_connection(device_id)
        if not is_connected:
            return False, error_msg
        
        # 尝试多种方法获取前台应用
        commands = [
            f"adb -s {device_id} shell dumpsys activity activities | grep 'mCurrentFocus'",
            f"adb -s {device_id} shell dumpsys window windows | grep 'mCurrentFocus'",
            f"adb -s {device_id} shell dumpsys activity | grep 'mFocusedActivity'",
        ]
        
        for command in commands:
            result = safe_subprocess_run(command, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                focus_info = result.stdout.strip()
                if focus_info and ('mCurrentFocus' in focus_info or 'mFocusedActivity' in focus_info):
                    # 解析包名和活动名
                    package_match = re.search(r'\{([^}]+)\}', focus_info)
                    if package_match:
                        package_info = package_match.group(1)
                        parts = package_info.split('/')
                        package_name = parts[0]
                        activity_name = parts[1] if len(parts) > 1 else ""
                        return True, f"包名: {package_name}, 活动名: {activity_name}"
        
        return False, "无法获取前台应用信息"
        
    except subprocess.TimeoutExpired:
        return False, "获取前台应用信息超时"
    except Exception as e:
        return False, f"获取前台应用信息失败: {str(e)}"


def get_app_version(device_id, package_name):
    """
    获取应用版本信息
    
    Args:
        device_id (str): 设备ID
        package_name (str): 应用包名
        
    Returns:
        tuple: (success, version_info)
    """
    try:
        # 首先检查设备连接
        is_connected, error_msg = check_device_connection(device_id)
        if not is_connected:
            return False, error_msg
        
        # 获取应用版本信息
        command = f"adb -s {device_id} shell dumpsys package {package_name}"
        result = safe_subprocess_run(command, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            # 提取版本号
            version_match = re.search(r'versionName=(\S+)', result.stdout)
            if version_match:
                version_name = version_match.group(1)
                return True, version_name
            else:
                return False, "无法获取版本信息"
        else:
            return False, f"应用 {package_name} 不存在或无法访问"
            
    except subprocess.TimeoutExpired:
        return False, "获取应用版本信息超时"
    except Exception as e:
        return False, f"获取应用版本信息失败: {str(e)}"


def execute_adb_command(device_id, command, timeout=30):
    """
    执行ADB命令
    
    Args:
        device_id (str): 设备ID
        command (str): 要执行的命令
        timeout (int): 超时时间（秒）
        
    Returns:
        tuple: (success, result_info)
    """
    try:
        # 首先检查设备连接
        is_connected, error_msg = check_device_connection(device_id)
        if not is_connected:
            return False, error_msg
        
        full_command = f"adb -s {device_id} {command}"
        result = safe_subprocess_run(full_command, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
            
    except subprocess.TimeoutExpired:
        return False, f"命令执行超时 ({timeout}秒)"
    except Exception as e:
        return False, f"命令执行失败: {str(e)}"