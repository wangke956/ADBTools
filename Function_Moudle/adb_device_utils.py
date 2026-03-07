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
        
        # 方法1: 使用 dumpsys activity top (更可靠)
        command = f"adb -s {device_id} shell dumpsys activity top"
        result = safe_subprocess_run(command, capture_output=True, text=True, timeout=30)
        
        focus_info = None
        if result.returncode == 0 and result.stdout:
            # 在 Python 中过滤包含 ACTIVITY 的行
            for line in result.stdout.split('\n'):
                if 'ACTIVITY' in line:
                    focus_info = line.strip()
                    break
        
        # 方法2: 如果方法1失败，尝试 dumpsys window
        if not focus_info:
            command2 = f"adb -s {device_id} shell dumpsys window windows"
            result2 = safe_subprocess_run(command2, capture_output=True, text=True, timeout=30)
            
            if result2.returncode == 0 and result2.stdout:
                for line in result2.stdout.split('\n'):
                    if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                        focus_info = line.strip()
                        break
        
        if not focus_info:
            return False, "无法获取前台应用信息"
        
        # 解析包名和活动名
        package_name = None
        activity_name = None
        
        # 尝试匹配 ACTIVITY 格式
        activity_match = re.search(r'ACTIVITY\s+(\S+)', focus_info)
        if activity_match:
            full_name = activity_match.group(1)
            if '/' in full_name:
                parts = full_name.split('/')
                package_name = parts[0]
                activity_name = parts[1] if len(parts) > 1 else ""
            else:
                package_name = full_name
        
        # 尝试匹配 mCurrentFocus 格式
        if not package_name:
            focus_match = re.search(r'\{[^}]*\s+(\S+)/(\S*)\}', focus_info)
            if focus_match:
                package_name = focus_match.group(1)
                activity_name = focus_match.group(2) if focus_match.group(2) else ""
        
        if package_name:
            if activity_name:
                return True, f"包名: {package_name}, 活动名: {activity_name}"
            else:
                return True, f"包名: {package_name}"
        
        return False, "无法解析前台应用信息"
        
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