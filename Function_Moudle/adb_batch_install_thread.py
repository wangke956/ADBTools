from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import os
import sys
import re

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from adb_utils import adb_utils
except ImportError:
    # 如果导入失败，创建简单的回退
    class ADBUtilsFallback:
        @staticmethod
        def run_adb_command(command, device_id=None, **kwargs):
            adb_cmd = "adb"
            if device_id:
                full_command = f'{adb_cmd} -s {device_id} {command}'
            else:
                full_command = f'{adb_cmd} {command}'
            
            default_kwargs = {
                'shell': True,
                'capture_output': True,
                'text': True,
                'encoding': 'utf-8',
                'errors': 'ignore'
            }
            default_kwargs.update(kwargs)
            
            return subprocess.run(full_command, **default_kwargs)
    
    adb_utils = ADBUtilsFallback()

# 导入配置管理器
try:
    from config_manager import config_manager
except ImportError:
    # 如果导入失败，创建简单的回退配置
    class ConfigManagerFallback:
        def get(self, key, default=None):
            # 默认的特殊包名配置
            if key == "batch_install.special_packages":
                return {
                    "@com.saicmotor.voiceservice": {
                        "delete_before_push": False,
                        "description": "voiceservice包，只push不删除"
                    },
                    "@com.saicmotor.adapterservice": {
                        "delete_before_push": True,
                        "description": "adapterservice包，先删除再push"
                    }
                }
            return default
    
    config_manager = ConfigManagerFallback()


class ADBBatchInstallThread(QThread):
    """批量安装APK文件的线程"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    file_progress_signal = pyqtSignal(str, str)  # (文件名, 状态)
    overall_progress_signal = pyqtSignal(int, int)  # (当前进度, 总文件数)
    realtime_output_signal = pyqtSignal(str)  # 实时输出信号

    def __init__(self, device_id, folder_path, connection_mode='adb', u2_device=None, allow_downgrade=False):
        """
        初始化线程
        
        Args:
            device_id: 设备ID
            folder_path: 文件夹路径
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: u2设备对象（仅当connection_mode='u2'时使用）
            allow_downgrade: 是否允许降级安装，默认为False
        """
        super(ADBBatchInstallThread, self).__init__()
        self.device_id = device_id
        self.folder_path = folder_path
        self.connection_mode = connection_mode
        self.u2_device = u2_device
        self.allow_downgrade = allow_downgrade
        
        # 从配置文件读取特殊处理的包名配置
        self.special_packages_config = config_manager.get("batch_install.special_packages", {
            "@com.saicmotor.voiceservice": {
                "delete_before_push": False,
                "description": "voiceservice包，只push不删除"
            },
            "@com.saicmotor.adapterservice": {
                "delete_before_push": True,
                "description": "adapterservice包，先删除再push"
            }
        })

    def _execute_adb_command(self, command, realtime=False):
        """执行ADB命令
        
        Args:
            command: ADB命令
            realtime: 是否实时输出，默认为False
        """
        try:
            if realtime:
                # 实时输出模式
                def output_callback(line):
                    self.realtime_output_signal.emit(line)
                
                result = adb_utils.run_adb_command_realtime(
                    command, 
                    self.device_id,
                    output_callback=output_callback
                )
            else:
                # 普通模式
                result = adb_utils.run_adb_command(command, self.device_id)
            return result
        except Exception as e:
            self.error_signal.emit(f"执行ADB命令失败: {str(e)}")
            return None

    def _execute_u2_command(self, command):
        """通过u2执行命令"""
        try:
            # u2模式下，使用shell命令执行
            result = self.u2_device.shell(command)
            return result
        except Exception as e:
            self.error_signal.emit(f"执行u2命令失败: {str(e)}")
            return None

    def _execute_command(self, command, realtime=False):
        """根据连接模式执行命令
        
        Args:
            command: 命令
            realtime: 是否实时输出，默认为False
        """
        if self.connection_mode == 'u2' and self.u2_device:
            return self._execute_u2_command(command)
        else:
            return self._execute_adb_command(command, realtime=realtime)

    def _get_apk_package_name(self, apk_path):
        """获取APK文件的包名"""
        try:
            # 使用aapt工具获取包名
            quoted_apk_path = f'"{apk_path}"'
            command = f"aapt dump badging {quoted_apk_path} | findstr name"
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore'
            )
            
            if result.returncode != 0:
                self.error_signal.emit(f"获取APK包名失败: {result.stderr}")
                return None
            
            # 解析包名
            output = result.stdout.strip()
            match = re.search(r"name='([^']+)'", output)
            if match:
                package_name = match.group(1)
                return package_name
            else:
                self.error_signal.emit(f"无法解析APK包名: {output}")
                return None
                
        except Exception as e:
            self.error_signal.emit(f"获取APK包名时发生错误: {str(e)}")
            return None

    def _get_package_install_path(self, package_name):
        """获取包名的安装路径和文件名
        
        Returns:
            tuple: (完整apk路径, apk文件名) 或 None
        """
        try:
            command = f"shell pm path {package_name}"
            
            # 显示要执行的adb命令
            self.progress_signal.emit(f"执行命令: adb -s {self.device_id} {command}")
            
            # 执行adb shell pm path <包名> 命令
            result = self._execute_command(command)
            
            if result is None:
                return None
            
            if self.connection_mode == 'u2':
                output = str(result).strip()
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result).strip()
            
            # 显示完整的返回结果
            self.progress_signal.emit(f"命令返回: {output}")
            
            # 解析路径，格式通常是：package:/data/app/包名-xxx/base.apk
            if output.startswith("package:"):
                apk_path = output.replace("package:", "").strip()
                # 获取文件名
                apk_filename = os.path.basename(apk_path)
                self.progress_signal.emit(f"解析出的安装路径: {apk_path}")
                self.progress_signal.emit(f"APK文件名: {apk_filename}")
                return (apk_path, apk_filename)
            else:
                self.progress_signal.emit(f"未找到包 {package_name} 的安装路径")
                return None
                
        except Exception as e:
            self.error_signal.emit(f"获取包安装路径失败: {str(e)}")
            return None

    def _install_apk(self, apk_path, allow_downgrade=False):
        """安装APK文件
        
        Args:
            apk_path: APK文件路径
            allow_downgrade: 是否允许降级安装，默认为False
        """
        try:
            quoted_apk_path = f'"{apk_path}"'
            
            # 构建安装命令
            if allow_downgrade:
                command = f"install -r -d {quoted_apk_path}"
                self.progress_signal.emit("使用降级安装模式 (-r -d)")
            else:
                command = f"install -r {quoted_apk_path}"
                self.progress_signal.emit("使用普通安装模式 (-r)")
            
            # 显示要执行的adb命令
            self.progress_signal.emit(f"执行命令: adb -s {self.device_id} {command}")
            
            # 使用实时输出执行命令
            result = self._execute_command(command, realtime=True)
            
            if result is None:
                return False
            
            if self.connection_mode == 'u2':
                output = str(result)
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result)
            
            # 显示完整的返回结果
            self.progress_signal.emit(f"命令返回: {output}")
            
            if "Success" in output or "success" in output.lower():
                self.progress_signal.emit("安装成功！")
                return True
            else:
                self.error_signal.emit(f"安装失败: {output}")
                return False
                
        except Exception as e:
            self.error_signal.emit(f"安装APK时发生错误: {str(e)}")
            return False

    def _push_apk_to_path(self, apk_path, target_path):
        """将APK文件push到指定路径"""
        try:
            quoted_apk_path = f'"{apk_path}"'
            command = f"push {quoted_apk_path} {target_path}"
            
            # 显示要执行的adb命令
            self.progress_signal.emit(f"执行命令: adb -s {self.device_id} {command}")
            
            # 使用实时输出执行命令
            result = self._execute_command(command, realtime=True)
            
            if result is None:
                return False
            
            if self.connection_mode == 'u2':
                output = str(result)
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result)
            
            # 显示完整的返回结果
            self.progress_signal.emit(f"命令返回: {output}")
            
            if "pushed" in output.lower() or "success" in output.lower():
                self.progress_signal.emit("push成功！")
                return True
            else:
                self.error_signal.emit(f"push失败: {output}")
                return False
                
        except Exception as e:
            self.error_signal.emit(f"push APK时发生错误: {str(e)}")
            return False

    def _delete_device_apk(self, apk_path):
        """删除设备上的APK文件"""
        try:
            command = f"shell rm -f {apk_path}"
            
            # 显示要执行的adb命令
            self.progress_signal.emit(f"执行命令: adb -s {self.device_id} {command}")
            
            # 执行删除命令
            result = self._execute_command(command)
            
            if result is None:
                return False
            
            if self.connection_mode == 'u2':
                output = str(result)
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result)
            
            # 显示完整的返回结果
            self.progress_signal.emit(f"命令返回: {output}")
            
            # 检查是否删除成功
            if "No such file or directory" in output:
                self.progress_signal.emit(f"文件不存在: {apk_path}")
                return True  # 文件不存在也算成功
            elif "Permission denied" in output:
                self.error_signal.emit(f"权限不足，无法删除文件: {apk_path}")
                return False
            else:
                self.progress_signal.emit("删除成功！")
                return True
                
        except Exception as e:
            self.error_signal.emit(f"删除设备APK时发生错误: {str(e)}")
            return False

    def _scan_apk_files(self):
        """扫描文件夹下的所有APK文件"""
        apk_files = []
        
        try:
            if not os.path.exists(self.folder_path):
                self.error_signal.emit(f"文件夹不存在: {self.folder_path}")
                return []
            
            if not os.path.isdir(self.folder_path):
                self.error_signal.emit(f"路径不是文件夹: {self.folder_path}")
                return []
            
            # 扫描所有.apk文件
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.lower().endswith('.apk'):
                        apk_path = os.path.join(root, file)
                        apk_files.append(apk_path)
            
            return apk_files
            
        except Exception as e:
            self.error_signal.emit(f"扫描APK文件时发生错误: {str(e)}")
            return []

    def run(self):
        """线程主函数"""
        try:
            self.progress_signal.emit("开始扫描文件夹中的APK文件...")
            
            # 扫描APK文件
            apk_files = self._scan_apk_files()
            
            if not apk_files:
                self.error_signal.emit("未找到APK文件")
                return
            
            total_files = len(apk_files)
            self.progress_signal.emit(f"找到 {total_files} 个APK文件")
            self.overall_progress_signal.emit(0, total_files)
            
            success_count = 0
            fail_count = 0
            special_count = 0
            
            for index, apk_path in enumerate(apk_files):
                file_name = os.path.basename(apk_path)
                self.progress_signal.emit(f"处理文件 ({index+1}/{total_files}): {file_name}")
                self.file_progress_signal.emit(file_name, "开始处理")
                
                # 更新总体进度
                self.overall_progress_signal.emit(index + 1, total_files)
                
                # 获取包名
                package_name = self._get_apk_package_name(apk_path)
                
                if package_name is None:
                    self.file_progress_signal.emit(file_name, "获取包名失败")
                    fail_count += 1
                    continue
                
                self.progress_signal.emit(f"  包名: {package_name}")
                
                # 检查是否为特殊包名，并获取配置信息
                special_config = None
                for config_key, config_value in self.special_packages_config.items():
                    if package_name == config_key.replace("@", ""):
                        special_config = config_value
                        break
                
                if special_config:
                    special_count += 1
                    
                    # 从配置中获取是否删除原文件
                    delete_before_push = special_config.get("delete_before_push", False)
                    description = special_config.get("description", "")
                    
                    self.progress_signal.emit(f"  检测到特殊包名: {package_name}")
                    if description:
                        self.progress_signal.emit(f"  配置说明: {description}")
                    self.progress_signal.emit(f"  删除原文件: {'是' if delete_before_push else '否'}")
                    
                    # 获取安装路径和文件名
                    install_info = self._get_package_install_path(package_name)
                    
                    if install_info is None:
                        self.progress_signal.emit(f"  无法获取安装路径，尝试普通安装")
                        # 如果无法获取路径，回退到普通安装
                        success = self._install_apk(apk_path, self.allow_downgrade)
                    else:
                        device_apk_path, device_apk_filename = install_info
                        self.progress_signal.emit(f"  设备APK路径: {device_apk_path}")
                        self.progress_signal.emit(f"  设备APK文件名: {device_apk_filename}")
                        
                        # 根据配置决定是否删除原文件
                        if delete_before_push:
                            self.progress_signal.emit(f"  步骤1: 删除设备上的APK文件")
                            delete_success = self._delete_device_apk(device_apk_path)
                            
                            if not delete_success:
                                self.progress_signal.emit(f"  删除设备APK失败，尝试普通安装")
                                success = self._install_apk(apk_path, self.allow_downgrade)
                            else:
                                # 2. 将本地apk push到设备，使用原文件名
                                # 获取目标路径（目录路径）
                                target_dir = os.path.dirname(device_apk_path)
                                target_path = f"{target_dir}/{device_apk_filename}"
                                
                                self.progress_signal.emit(f"  步骤2: 将本地APK push到设备")
                                self.progress_signal.emit(f"  目标路径: {target_path}")
                                success = self._push_apk_to_path(apk_path, target_path)
                        else:
                            # 不删除原文件，直接push
                            # 获取目标路径（目录路径）
                            target_dir = os.path.dirname(device_apk_path)
                            target_path = f"{target_dir}/{device_apk_filename}"
                            
                            self.progress_signal.emit(f"  执行push操作（不删除原文件）")
                            self.progress_signal.emit(f"  目标路径: {target_path}")
                            success = self._push_apk_to_path(apk_path, target_path)
                else:
                    self.progress_signal.emit(f"  执行普通安装")
                    # 执行普通安装
                    success = self._install_apk(apk_path, self.allow_downgrade)
                
                # 更新文件状态
                if success:
                    self.file_progress_signal.emit(file_name, "成功")
                    success_count += 1
                else:
                    self.file_progress_signal.emit(file_name, "失败")
                    fail_count += 1
            
            # 输出最终结果
            self.result_signal.emit(f"批量安装完成！\n"
                                  f"总文件数: {total_files}\n"
                                  f"成功: {success_count}\n"
                                  f"失败: {fail_count}\n"
                                  f"特殊处理: {special_count}")
            
        except Exception as e:
            self.error_signal.emit(f"批量安装过程中发生错误: {str(e)}")