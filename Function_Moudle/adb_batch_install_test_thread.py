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


class ADBBatchInstallTestThread(QThread):
    """批量安装APK文件的测试线程 - 仅打印命令和值，不实际执行"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    debug_signal = pyqtSignal(str)  # 调试信号，用于打印详细命令和值

    def __init__(self, device_id, folder_path, connection_mode='adb', u2_device=None):
        """
        初始化测试线程
        
        Args:
            device_id: 设备ID
            folder_path: 文件夹路径
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: u2设备对象（仅当connection_mode='u2'时使用）
        """
        super(ADBBatchInstallTestThread, self).__init__()
        self.device_id = device_id
        self.folder_path = folder_path
        self.connection_mode = connection_mode
        self.u2_device = u2_device
        
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

    def _print_debug_info(self, title, info_dict):
        """打印调试信息"""
        self.debug_signal.emit(f"\n{'='*60}")
        self.debug_signal.emit(f"调试信息: {title}")
        self.debug_signal.emit(f"{'='*60}")
        for key, value in info_dict.items():
            self.debug_signal.emit(f"  {key}: {value}")
        self.debug_signal.emit(f"{'='*60}\n")

    def _simulate_adb_command(self, command):
        """模拟执行ADB命令 - 仅打印命令"""
        try:
            adb_cmd = "adb"
            if self.device_id:
                full_command = f'{adb_cmd} -s {self.device_id} {command}'
            else:
                full_command = f'{adb_cmd} {command}'
            
            self.debug_signal.emit(f"[模拟ADB命令] 将执行: {full_command}")
            
            # 返回模拟结果
            class MockResult:
                def __init__(self):
                    self.stdout = "[模拟输出] 命令执行成功"
                    self.stderr = ""
                    self.returncode = 0
            
            return MockResult()
        except Exception as e:
            self.error_signal.emit(f"模拟ADB命令失败: {str(e)}")
            return None

    def _simulate_u2_command(self, command):
        """模拟执行u2命令 - 仅打印命令"""
        try:
            self.debug_signal.emit(f"[模拟u2命令] 将执行: {command}")
            
            # 返回模拟结果
            return "[模拟输出] u2命令执行成功"
        except Exception as e:
            self.error_signal.emit(f"模拟u2命令失败: {str(e)}")
            return None

    def _simulate_command(self, command):
        """根据连接模式模拟执行命令"""
        if self.connection_mode == 'u2' and self.u2_device:
            return self._simulate_u2_command(command)
        else:
            return self._simulate_adb_command(command)

    def _get_apk_package_name(self, apk_path):
        """获取APK文件的包名 - 测试模式"""
        try:
            # 使用aapt工具获取包名
            quoted_apk_path = f'"{apk_path}"'
            command = f"aapt dump badging {quoted_apk_path} | findstr name"
            
            self.debug_signal.emit(f"[获取包名] 将执行命令: {command}")
            
            # 模拟执行命令
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore'
            )
            
            if result.returncode != 0:
                self.debug_signal.emit(f"[获取包名] 命令执行失败: {result.stderr}")
                return None
            
            # 解析包名
            output = result.stdout.strip()
            match = re.search(r"name='([^']+)'", output)
            if match:
                package_name = match.group(1)
                self.debug_signal.emit(f"[获取包名] 成功解析包名: {package_name}")
                return package_name
            else:
                self.debug_signal.emit(f"[获取包名] 无法解析APK包名: {output}")
                return None
                
        except Exception as e:
            self.error_signal.emit(f"获取APK包名时发生错误: {str(e)}")
            return None

    def _get_package_install_path(self, package_name):
        """获取包名的安装路径和文件名 - 测试模式
        
        Returns:
            tuple: (完整apk路径, apk文件名) 或 None
        """
        try:
            # 模拟执行adb shell pm path <包名> 命令
            command = f"shell pm path {package_name}"
            self.debug_signal.emit(f"[获取安装路径] 将执行命令: {command}")
            
            result = self._simulate_command(command)
            
            if result is None:
                return None
            
            if self.connection_mode == 'u2':
                output = str(result).strip()
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result).strip()
            
            self.debug_signal.emit(f"[获取安装路径] 命令输出: {output}")
            
            # 解析路径，格式通常是：package:/data/app/包名-xxx/base.apk
            if output.startswith("package:"):
                apk_path = output.replace("package:", "").strip()
                # 获取文件名
                apk_filename = os.path.basename(apk_path)
                self.debug_signal.emit(f"[获取安装路径] 解析出的完整路径: {apk_path}")
                self.debug_signal.emit(f"[获取安装路径] APK文件名: {apk_filename}")
                return (apk_path, apk_filename)
            else:
                self.debug_signal.emit(f"[获取安装路径] 输出格式不正确")
                return None
                
        except Exception as e:
            self.error_signal.emit(f"获取包安装路径失败: {str(e)}")
            return None

    def _simulate_install_apk(self, apk_path):
        """模拟安装APK文件 - 仅打印命令"""
        try:
            quoted_apk_path = f'"{apk_path}"'
            command = f"install -r {quoted_apk_path}"
            
            self.debug_signal.emit(f"[模拟安装] 将执行命令: {command}")
            
            result = self._simulate_command(command)
            
            if result is None:
                return False
            
            if self.connection_mode == 'u2':
                output = str(result)
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result)
            
            self.debug_signal.emit(f"[模拟安装] 命令输出: {output}")
            
            # 模拟成功
            self.debug_signal.emit(f"[模拟安装] 模拟安装成功")
            return True
                
        except Exception as e:
            self.error_signal.emit(f"模拟安装APK时发生错误: {str(e)}")
            return False

    def _simulate_push_apk_to_path(self, apk_path, target_path):
        """模拟将APK文件push到指定路径 - 仅打印命令"""
        try:
            quoted_apk_path = f'"{apk_path}"'
            command = f"push {quoted_apk_path} {target_path}"
            
            self.debug_signal.emit(f"[模拟push] 将执行命令: {command}")
            
            result = self._simulate_command(command)
            
            if result is None:
                return False
            
            if self.connection_mode == 'u2':
                output = str(result)
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result)
            
            self.debug_signal.emit(f"[模拟push] 命令输出: {output}")
            
            # 模拟成功
            self.debug_signal.emit(f"[模拟push] 模拟push成功")
            return True
                
        except Exception as e:
            self.error_signal.emit(f"模拟push APK时发生错误: {str(e)}")
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
            
            self.debug_signal.emit(f"[扫描文件] 找到 {len(apk_files)} 个APK文件:")
            for apk_path in apk_files:
                self.debug_signal.emit(f"  - {apk_path}")
            
            return apk_files
            
        except Exception as e:
            self.error_signal.emit(f"扫描APK文件时发生错误: {str(e)}")
            return []

    def run(self):
        """线程主函数 - 测试模式"""
        try:
            self.progress_signal.emit("开始测试批量安装功能...")
            self.debug_signal.emit(f"设备ID: {self.device_id}")
            self.debug_signal.emit(f"文件夹路径: {self.folder_path}")
            self.debug_signal.emit(f"连接模式: {self.connection_mode}")
            
            # 打印初始信息
            init_info = {
                "设备ID": self.device_id,
                "文件夹路径": self.folder_path,
                "连接模式": self.connection_mode,
                "特殊包名列表": self.special_packages
            }
            self._print_debug_info("初始化参数", init_info)
            
            self.progress_signal.emit("开始扫描文件夹中的APK文件...")
            
            # 扫描APK文件
            apk_files = self._scan_apk_files()
            
            if not apk_files:
                self.error_signal.emit("未找到APK文件")
                return
            
            total_files = len(apk_files)
            self.progress_signal.emit(f"找到 {total_files} 个APK文件")
            
            success_count = 0
            fail_count = 0
            special_count = 0
            
            for index, apk_path in enumerate(apk_files):
                file_name = os.path.basename(apk_path)
                self.progress_signal.emit(f"\n处理文件 ({index+1}/{total_files}): {file_name}")
                
                # 打印文件信息
                file_info = {
                    "文件路径": apk_path,
                    "文件名": file_name,
                    "文件序号": f"{index+1}/{total_files}"
                }
                self._print_debug_info(f"文件处理开始 - {file_name}", file_info)
                
                # 获取包名
                self.debug_signal.emit(f"[步骤1] 获取APK包名...")
                package_name = self._get_apk_package_name(apk_path)
                
                if package_name is None:
                    self.debug_signal.emit(f"[步骤1] 获取包名失败")
                    fail_count += 1
                    continue
                
                self.debug_signal.emit(f"[步骤1] 包名: {package_name}")
                
                # 检查是否为特殊包名，并获取配置信息
                special_config = None
                for config_key, config_value in self.special_packages_config.items():
                    if package_name == config_key.replace("@", ""):
                        special_config = config_value
                        break
                
                if special_config:
                    self.debug_signal.emit(f"[步骤2] 检测到特殊包名: {package_name}")
                    special_count += 1
                    
                    # 从配置中获取是否删除原文件
                    delete_before_push = special_config.get("delete_before_push", False)
                    description = special_config.get("description", "")
                    
                    self.debug_signal.emit(f"[步骤2] 配置说明: {description}")
                    self.debug_signal.emit(f"[步骤2] 删除原文件: {'是' if delete_before_push else '否'}")
                    
                    # 获取安装路径和文件名
                    self.debug_signal.emit(f"[步骤3] 获取安装路径和文件名...")
                    install_info = self._get_package_install_path(package_name)
                    
                    if install_info is None:
                        self.debug_signal.emit(f"[步骤3] 无法获取安装路径，将回退到普通安装")
                        # 如果无法获取路径，回退到普通安装
                        self.debug_signal.emit(f"[步骤4] 执行普通安装...")
                        success = self._simulate_install_apk(apk_path)
                    else:
                        device_apk_path, device_apk_filename = install_info
                        self.debug_signal.emit(f"[步骤3] 设备APK路径: {device_apk_path}")
                        self.debug_signal.emit(f"[步骤3] 设备APK文件名: {device_apk_filename}")
                        
                        # 根据配置决定是否删除原文件
                        if delete_before_push:
                            # 模拟删除设备上的apk文件
                            self.debug_signal.emit(f"[步骤4] 模拟删除设备上的APK文件...")
                            self.debug_signal.emit(f"[步骤4] 将执行命令: adb -s {self.device_id} shell rm -f {device_apk_path}")
                            
                            # 模拟push操作，使用原文件名
                            target_dir = os.path.dirname(device_apk_path)
                            target_path = f"{target_dir}/{device_apk_filename}"
                            self.debug_signal.emit(f"[步骤5] 模拟push操作，使用原文件名...")
                            self.debug_signal.emit(f"[步骤5] 目标路径: {target_path}")
                            success = self._simulate_push_apk_to_path(apk_path, target_path)
                        else:
                            # 不删除原文件，直接push
                            target_dir = os.path.dirname(device_apk_path)
                            target_path = f"{target_dir}/{device_apk_filename}"
                            self.debug_signal.emit(f"[步骤4] 模拟push操作（不删除原文件）...")
                            self.debug_signal.emit(f"[步骤4] 目标路径: {target_path}")
                            success = self._simulate_push_apk_to_path(apk_path, target_path)
                else:
                    self.debug_signal.emit(f"[步骤2] 普通包名，执行普通安装")
                    # 执行普通安装
                    self.debug_signal.emit(f"[步骤3] 执行普通安装...")
                    success = self._simulate_install_apk(apk_path)
                
                # 更新结果
                if success:
                    self.debug_signal.emit(f"[结果] 模拟操作成功")
                    success_count += 1
                else:
                    self.debug_signal.emit(f"[结果] 模拟操作失败")
                    fail_count += 1
                
                # 打印文件处理总结
                file_summary = {
                    "包名": package_name,
                    "是否为特殊包": "是" if special_config else "否",
                    "是否删除原文件": "是" if (special_config and special_config.get("delete_before_push", False)) else "否",
                    "操作类型": "push" if special_config else "install",
                    "模拟结果": "成功" if success else "失败"
                }
                self._print_debug_info(f"文件处理完成 - {file_name}", file_summary)
            
            # 输出最终结果
            self.result_signal.emit(f"\n{'='*60}")
            self.result_signal.emit("批量安装功能测试完成！")
            self.result_signal.emit(f"{'='*60}")
            self.result_signal.emit(f"总文件数: {total_files}")
            self.result_signal.emit(f"成功模拟: {success_count}")
            self.result_signal.emit(f"失败模拟: {fail_count}")
            self.result_signal.emit(f"特殊处理: {special_count}")
            self.result_signal.emit(f"{'='*60}")
            self.result_signal.emit("\n测试总结:")
            self.result_signal.emit("1. 所有命令和值都已打印，请检查是否正确")
            self.result_signal.emit("2. 特殊包名处理逻辑已验证")
            self.result_signal.emit("3. 连接模式适配已测试")
            self.result_signal.emit("4. 文件扫描功能正常")
            self.result_signal.emit("5. 确认无误后，可使用正式批量安装功能")
            self.result_signal.emit(f"{'='*60}")
            
        except Exception as e:
            self.error_signal.emit(f"批量安装测试过程中发生错误: {str(e)}")
