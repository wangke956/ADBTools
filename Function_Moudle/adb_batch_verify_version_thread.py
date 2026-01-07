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


class ADBBatchVerifyVersionThread(QThread):
    """批量验证APK版本号线程 - 检查APK文件版本号与设备中版本号是否一致"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    verify_result_signal = pyqtSignal(str)  # 验证结果信号

    def __init__(self, device_id, folder_path, connection_mode='adb', u2_device=None):
        """
        初始化验证线程
        
        Args:
            device_id: 设备ID
            folder_path: 文件夹路径
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: u2设备对象（仅当connection_mode='u2'时使用）
        """
        super(ADBBatchVerifyVersionThread, self).__init__()
        self.device_id = device_id
        self.folder_path = folder_path
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def _get_apk_package_and_version(self, apk_path):
        """获取APK文件的包名和版本号"""
        try:
            # 检查aapt工具是否可用
            try:
                aapt_check = subprocess.run(
                    "aapt version",
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                if aapt_check.returncode != 0:
                    self.error_signal.emit("[警告] aapt工具可能未安装或不在PATH中")
            except:
                self.error_signal.emit("[警告] 无法检查aapt工具，可能未安装")
            
            # 使用aapt工具获取包名和版本号
            quoted_apk_path = f'"{apk_path}"'
            command = f"aapt dump badging {quoted_apk_path}"
            
            self.progress_signal.emit(f"[获取APK信息] 执行命令: {command}")
            
            # 执行命令
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore'
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "不是内部或外部命令" in error_msg or "command not found" in error_msg:
                    self.error_signal.emit(f"[获取APK信息] aapt工具未找到，请安装Android SDK Build Tools")
                    self.error_signal.emit(f"[获取APK信息] 或者将aapt.exe添加到系统PATH中")
                else:
                    self.error_signal.emit(f"[获取APK信息] 命令执行失败: {error_msg}")
                return None, None
            
            # 解析包名和版本号
            output = result.stdout.strip()
            
            # 查找包名
            package_match = re.search(r"name='([^']+)'", output)
            package_name = package_match.group(1) if package_match else None
            
            # 查找版本号
            version_match = re.search(r"versionName='([^']+)'", output)
            version_name = version_match.group(1) if version_match else None
            
            if package_name:
                self.progress_signal.emit(f"[获取APK信息] 包名: {package_name}")
            else:
                self.error_signal.emit(f"[获取APK信息] 无法解析APK包名")
                
            if version_name:
                self.progress_signal.emit(f"[获取APK信息] 版本号: {version_name}")
            else:
                self.error_signal.emit(f"[获取APK信息] 无法解析APK版本号")
                
            return package_name, version_name
                
        except Exception as e:
            self.error_signal.emit(f"获取APK包名和版本号时发生错误: {str(e)}")
            return None, None

    def _get_device_package_version(self, package_name):
        """从设备获取指定包名的版本号"""
        try:
            if self.connection_mode == 'u2' and self.u2_device:
                # 使用u2接口获取应用信息
                app_info = self.u2_device.app_info(package_name)
                if app_info is None:
                    self.error_signal.emit(f"[设备查询] 应用 {package_name} 不存在")
                    return None
                
                version_name = app_info.get('versionName', '未知版本')
                self.progress_signal.emit(f"[设备查询] u2获取版本号: {version_name}")
                return version_name
                
            elif self.connection_mode == 'adb':
                # 使用ADB命令获取应用版本信息
                command = f"shell dumpsys package {package_name} | findstr versionName"
                
                self.progress_signal.emit(f"[设备查询] 执行命令: {command}")
                
                result = adb_utils.run_adb_command(
                    command, 
                    device_id=self.device_id,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode != 0:
                    self.error_signal.emit(f"[设备查询] 命令执行失败: {result.stderr}")
                    return None
                
                # 解析版本号
                output = result.stdout.strip()
                version_match = re.search(r'versionName=([^\s]+)', output)
                
                if version_match:
                    version_name = version_match.group(1)
                    self.progress_signal.emit(f"[设备查询] ADB获取版本号: {version_name}")
                    return version_name
                else:
                    self.error_signal.emit(f"[设备查询] 无法解析设备版本号: {output}")
                    return None
            else:
                self.error_signal.emit(f"[设备查询] 未知连接模式: {self.connection_mode}")
                return None
                
        except Exception as e:
            self.error_signal.emit(f"从设备获取包版本号时发生错误: {str(e)}")
            return None

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
            
            self.progress_signal.emit(f"[扫描文件] 找到 {len(apk_files)} 个APK文件:")
            for apk_path in apk_files:
                self.progress_signal.emit(f"  - {os.path.basename(apk_path)}")
            
            return apk_files
            
        except Exception as e:
            self.error_signal.emit(f"扫描APK文件时发生错误: {str(e)}")
            return []

    def _compare_versions(self, apk_version, device_version):
        """比较两个版本号是否一致"""
        if apk_version is None or device_version is None:
            return False
        
        # 简单字符串比较
        return apk_version.strip() == device_version.strip()

    def run(self):
        """线程主函数 - 验证版本号"""
        try:
            self.progress_signal.emit("开始验证批量推包版本号...")
            self.progress_signal.emit(f"设备ID: {self.device_id}")
            self.progress_signal.emit(f"文件夹路径: {self.folder_path}")
            self.progress_signal.emit(f"连接模式: {self.connection_mode}")
            
            self.progress_signal.emit("开始扫描文件夹中的APK文件...")
            
            # 扫描APK文件
            apk_files = self._scan_apk_files()
            
            if not apk_files:
                self.error_signal.emit("未找到APK文件")
                return
            
            total_files = len(apk_files)
            self.progress_signal.emit(f"找到 {total_files} 个APK文件")
            
            # 存储验证结果
            verification_results = []
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            for index, apk_path in enumerate(apk_files):
                file_name = os.path.basename(apk_path)
                self.progress_signal.emit(f"\n处理文件 ({index+1}/{total_files}): {file_name}")
                
                # 获取APK包名和版本号
                self.progress_signal.emit(f"[步骤1] 提取APK包名和版本号...")
                package_name, apk_version = self._get_apk_package_and_version(apk_path)
                
                if package_name is None or apk_version is None:
                    self.error_signal.emit(f"[步骤1] 无法获取APK信息，跳过此文件")
                    verification_results.append({
                        'file_name': file_name,
                        'package_name': package_name or '未知',
                        'apk_version': apk_version or '未知',
                        'device_version': 'N/A',
                        'result': '失败',
                        'reason': '无法提取APK信息'
                    })
                    fail_count += 1
                    continue
                
                # 从设备获取版本号
                self.progress_signal.emit(f"[步骤2] 从设备查询包名: {package_name}")
                device_version = self._get_device_package_version(package_name)
                
                if device_version is None:
                    self.error_signal.emit(f"[步骤2] 设备上未找到此包或无法获取版本号")
                    verification_results.append({
                        'file_name': file_name,
                        'package_name': package_name,
                        'apk_version': apk_version,
                        'device_version': 'N/A',
                        'result': '失败',
                        'reason': '设备上未找到此包'
                    })
                    fail_count += 1
                    continue
                
                # 比较版本号
                self.progress_signal.emit(f"[步骤3] 比较版本号...")
                self.progress_signal.emit(f"  APK版本号: {apk_version}")
                self.progress_signal.emit(f"  设备版本号: {device_version}")
                
                is_match = self._compare_versions(apk_version, device_version)
                
                if is_match:
                    self.progress_signal.emit(f"[步骤3] 版本号匹配 ✓")
                    verification_results.append({
                        'file_name': file_name,
                        'package_name': package_name,
                        'apk_version': apk_version,
                        'device_version': device_version,
                        'result': '成功',
                        'reason': '版本号一致'
                    })
                    success_count += 1
                else:
                    self.error_signal.emit(f"[步骤3] 版本号不匹配 ✗")
                    verification_results.append({
                        'file_name': file_name,
                        'package_name': package_name,
                        'apk_version': apk_version,
                        'device_version': device_version,
                        'result': '失败',
                        'reason': '版本号不一致'
                    })
                    fail_count += 1
            
            # 输出验证结果
            self.result_signal.emit(f"\n{'='*80}")
            self.result_signal.emit("批量推包版本号验证完成！")
            self.result_signal.emit(f"{'='*80}")
            self.result_signal.emit(f"总文件数: {total_files}")
            self.result_signal.emit(f"验证成功: {success_count}")
            self.result_signal.emit(f"验证失败: {fail_count}")
            self.result_signal.emit(f"跳过文件: {skip_count}")
            self.result_signal.emit(f"{'='*80}")
            
            # 输出详细结果表格
            self.verify_result_signal.emit("\n详细验证结果:")
            self.verify_result_signal.emit(f"{'='*80}")
            self.verify_result_signal.emit(f"{'文件名':<30} {'包名':<35} {'APK版本':<15} {'设备版本':<15} {'结果':<8} {'原因'}")
            self.verify_result_signal.emit(f"{'-'*80}")
            
            for result in verification_results:
                file_name = result['file_name'][:27] + "..." if len(result['file_name']) > 30 else result['file_name']
                package_name = result['package_name'][:32] + "..." if len(result['package_name']) > 35 else result['package_name']
                apk_version = result['apk_version'][:12] + "..." if len(result['apk_version']) > 15 else result['apk_version']
                device_version = result['device_version'][:12] + "..." if len(result['device_version']) > 15 else result['device_version']
                result_text = result['result']
                reason = result['reason']
                
                self.verify_result_signal.emit(f"{file_name:<30} {package_name:<35} {apk_version:<15} {device_version:<15} {result_text:<8} {reason}")
            
            self.verify_result_signal.emit(f"{'='*80}")
            
            # 输出总结
            self.result_signal.emit("\n验证总结:")
            self.result_signal.emit(f"{'='*80}")
            if success_count == total_files:
                self.result_signal.emit("✓ 所有APK文件版本号与设备版本号一致！")
            elif fail_count > 0:
                self.result_signal.emit("✗ 部分APK文件版本号与设备版本号不一致，请检查以下文件:")
                for result in verification_results:
                    if result['result'] == '失败':
                        self.result_signal.emit(f"  - {result['file_name']}: {result['reason']}")
            else:
                self.result_signal.emit("⚠ 验证完成，但未找到可验证的文件")
            
            self.result_signal.emit(f"{'='*80}")
            
        except Exception as e:
            self.error_signal.emit(f"批量验证版本号过程中发生错误: {str(e)}")
