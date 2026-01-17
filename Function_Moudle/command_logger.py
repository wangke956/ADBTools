#!/usr/bin/env python3
"""
命令执行日志记录器 - 专门用于记录所有命令的详细执行信息

功能：
1. 记录每个命令的完整信息（命令、参数、设备ID等）
2. 记录命令执行结果（返回码、标准输出、错误输出）
3. 记录命令执行时间
4. 支持命令搜索和过滤
5. 生成命令执行报告
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from logger_manager import get_logger, log_operation

# 创建日志记录器
logger = get_logger("ADBTools.CommandLogger")


class CommandLogger:
    """命令执行日志记录器"""
    
    def __init__(self, log_file: str = "command_history.log"):
        self.log_file = log_file
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        try:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"创建日志目录失败: {e}")
    
    def log_command(self, command: str, device_id: Optional[str] = None,
                   full_command: Optional[str] = None, adb_path: Optional[str] = None,
                   returncode: Optional[int] = None, stdout: Optional[str] = None,
                   stderr: Optional[str] = None, execution_time: Optional[float] = None,
                   result: str = "unknown", thread_id: Optional[int] = None,
                   thread_name: Optional[str] = None, timestamp: Optional[str] = None):
        """
        记录命令执行信息
        
        Args:
            command: ADB命令
            device_id: 设备ID
            full_command: 完整命令
            adb_path: ADB路径
            returncode: 返回码
            stdout: 标准输出
            stderr: 错误输出
            execution_time: 执行时间（秒）
            result: 执行结果（success/failed/error）
            thread_id: 线程ID
            thread_name: 线程名称
            timestamp: 时间戳
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        if not thread_id:
            thread_id = __import__('threading').current_thread().ident
        
        if not thread_name:
            thread_name = __import__('threading').current_thread().name
        
        log_entry = {
            "timestamp": timestamp,
            "command": command,
            "device_id": device_id,
            "full_command": full_command,
            "adb_path": adb_path,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time": execution_time,
            "result": result,
            "thread_id": thread_id,
            "thread_name": thread_name
        }
        
        # 同时记录到日志文件和操作历史
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"写入命令历史失败: {e}")
        
        # 只记录到操作历史，不记录到主日志（避免重复）
        log_operation("adb_command_execution", {
            "command": command,
            "device_id": device_id,
            "returncode": returncode,
            "result": result,
            "execution_time": execution_time,
            "thread_id": thread_id,
            "thread_name": thread_name,
            "timestamp": timestamp
        }, device_id, result)
    
    def get_command_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取命令历史记录
        
        Args:
            limit: 获取记录数量
            
        Returns:
            命令历史列表
        """
        try:
            if not os.path.exists(self.log_file):
                return []
            
            commands = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        commands.append(json.loads(line.strip()))
                    except:
                        pass
            
            # 返回最近的记录
            return commands[-limit:] if len(commands) > limit else commands
        except Exception as e:
            logger.error(f"读取命令历史失败: {e}")
            return []
    
    def search_commands(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜索命令历史
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            匹配的命令列表
        """
        try:
            if not os.path.exists(self.log_file):
                return []
            
            results = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        cmd = json.loads(line.strip())
                        # 在命令、输出中搜索
                        if (keyword.lower() in str(cmd.get('command', '')).lower() or
                            keyword.lower() in str(cmd.get('stdout', '')).lower() or
                            keyword.lower() in str(cmd.get('stderr', '')).lower()):
                            results.append(cmd)
                            if len(results) >= limit:
                                break
                    except:
                        pass
            
            return results
        except Exception as e:
            logger.error(f"搜索命令历史失败: {e}")
            return []
    
    def get_failed_commands(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取失败的命令
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            失败的命令列表
        """
        try:
            if not os.path.exists(self.log_file):
                return []
            
            failed = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        cmd = json.loads(line.strip())
                        if cmd.get('result') in ['failed', 'error'] or cmd.get('returncode', 0) != 0:
                            failed.append(cmd)
                            if len(failed) >= limit:
                                break
                    except:
                        pass
            
            return failed
        except Exception as e:
            logger.error(f"获取失败命令失败: {e}")
            return []
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        生成命令执行报告
        
        Args:
            output_file: 输出文件路径（可选）
            
        Returns:
            报告内容
        """
        commands = self.get_command_history(1000)
        
        if not commands:
            report = "没有命令执行记录"
            return report
        
        # 统计信息
        total = len(commands)
        success = sum(1 for cmd in commands if cmd.get('result') == 'success')
        failed = sum(1 for cmd in commands if cmd.get('result') in ['failed', 'error'])
        
        # 按命令类型统计
        command_types = {}
        for cmd in commands:
            cmd_type = cmd.get('command', '').split()[0] if cmd.get('command') else 'unknown'
            command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
        
        # 生成报告
        report = []
        report.append("=" * 80)
        report.append("ADBTools 命令执行报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"统计记录数: {total}")
        report.append("")
        report.append("执行统计:")
        report.append(f"  成功: {success} ({success/total*100:.1f}%)")
        report.append(f"  失败: {failed} ({failed/total*100:.1f}%)")
        report.append("")
        report.append("命令类型统计:")
        for cmd_type, count in sorted(command_types.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {cmd_type}: {count} 次")
        report.append("")
        report.append("=" * 80)
        report.append("最近的命令执行记录:")
        report.append("=" * 80)
        
        for i, cmd in enumerate(commands[-10:], 1):
            report.append(f"\n[{i}] {cmd.get('timestamp', '')}")
            report.append(f"    命令: {cmd.get('command', '')}")
            report.append(f"    设备: {cmd.get('device_id', 'N/A')}")
            report.append(f"    返回码: {cmd.get('returncode', 'N/A')}")
            report.append(f"    结果: {cmd.get('result', 'N/A')}")
            if cmd.get('execution_time'):
                report.append(f"    耗时: {cmd['execution_time']:.3f} 秒")
        
        report.append("")
        report.append("=" * 80)
        
        report_text = '\n'.join(report)
        
        # 保存到文件
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                logger.info(f"命令执行报告已保存: {output_file}")
            except Exception as e:
                logger.error(f"保存报告失败: {e}")
        
        return report_text
    
    def clear_history(self):
        """清空命令历史"""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
                logger.info("命令历史已清空")
        except Exception as e:
            logger.error(f"清空命令历史失败: {e}")


# 全局命令日志记录器实例
command_logger = CommandLogger()


# 便捷函数
def log_command_execution(command: str, device_id: Optional[str] = None,
                         full_command: Optional[str] = None, adb_path: Optional[str] = None,
                         returncode: Optional[int] = None, stdout: Optional[str] = None,
                         stderr: Optional[str] = None, execution_time: Optional[float] = None,
                         result: str = "unknown", thread_id: Optional[int] = None,
                         thread_name: Optional[str] = None, timestamp: Optional[str] = None):
    """记录命令执行（便捷函数）"""
    command_logger.log_command(
        command, device_id, full_command, adb_path,
        returncode, stdout, stderr, execution_time, result,
        thread_id, thread_name, timestamp
    )


def get_command_history(limit: int = 100) -> List[Dict[str, Any]]:
    """获取命令历史（便捷函数）"""
    return command_logger.get_command_history(limit)


def search_commands(keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
    """搜索命令（便捷函数）"""
    return command_logger.search_commands(keyword, limit)


def generate_command_report(output_file: Optional[str] = None) -> str:
    """生成命令报告（便捷函数）"""
    return command_logger.generate_report(output_file)