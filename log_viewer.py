#!/usr/bin/env python3
"""
日志查看器 - 提供日志查看和分析功能

功能：
1. 查看应用日志
2. 查看操作历史
3. 查看性能统计
4. 日志搜索和过滤
5. 日志导出
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from logger_manager import logger_manager


class LogViewer:
    """日志查看器"""
    
    def __init__(self):
        self.log_dir = logger_manager.log_dir
    
    def get_log_files(self) -> List[str]:
        """获取所有日志文件"""
        try:
            log_dir = Path(self.log_dir)
            if not log_dir.exists():
                return []
            
            log_files = []
            for file in log_dir.glob("*.log"):
                log_files.append(str(file))
            
            return sorted(log_files, key=lambda x: os.path.getmtime(x), reverse=True)
        except Exception as e:
            print(f"获取日志文件失败: {e}")
            return []
    
    def read_log_file(self, file_path: str, max_lines: int = 1000) -> List[str]:
        """
        读取日志文件
        
        Args:
            file_path: 日志文件路径
            max_lines: 最大读取行数
            
        Returns:
            日志行列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 返回最后 max_lines 行
                return lines[-max_lines:] if len(lines) > max_lines else lines
        except Exception as e:
            print(f"读取日志文件失败: {e}")
            return []
    
    def search_logs(self, file_path: str, keyword: str) -> List[str]:
        """
        在日志文件中搜索关键词
        
        Args:
            file_path: 日志文件路径
            keyword: 搜索关键词
            
        Returns:
            匹配的行列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return [line for line in lines if keyword.lower() in line.lower()]
        except Exception as e:
            print(f"搜索日志失败: {e}")
            return []
    
    def get_operation_history(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        获取操作历史
        
        Args:
            count: 获取记录数量
            
        Returns:
            操作历史列表
        """
        if logger_manager.operation_logger:
            operations = logger_manager.operation_logger.get_recent_operations(count)
            # 解析JSON格式的操作记录
            parsed_operations = []
            for op in operations:
                if isinstance(op, str):
                    try:
                        parsed_operations.append(json.loads(op))
                    except:
                        pass
                else:
                    parsed_operations.append(op)
            return parsed_operations
        return []
    
    def get_performance_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Args:
            operation_name: 操作名称（可选，不指定则返回所有操作的统计）
            
        Returns:
            性能统计字典
        """
        if logger_manager.performance_monitor:
            return logger_manager.performance_monitor.get_statistics(operation_name)
        return {}
    
    def get_error_logs(self, file_path: str) -> List[str]:
        """
        获取错误日志
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            错误行列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return [line for line in lines if 'ERROR' in line or 'CRITICAL' in line]
        except Exception as e:
            print(f"获取错误日志失败: {e}")
            return []
    
    def get_warning_logs(self, file_path: str) -> List[str]:
        """
        获取警告日志
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            警告行列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return [line for line in lines if 'WARNING' in line]
        except Exception as e:
            print(f"获取警告日志失败: {e}")
            return []
    
    def export_logs(self, output_file: str, file_type: str = "txt") -> bool:
        """
        导出日志
        
        Args:
            output_file: 输出文件路径
            file_type: 文件类型（txt/json）
            
        Returns:
            是否成功
        """
        try:
            log_files = self.get_log_files()
            
            if file_type == "json":
                # 导出为JSON格式
                all_logs = []
                for log_file in log_files:
                    lines = self.read_log_file(log_file)
                    all_logs.extend(lines)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "log_files": log_files,
                        "logs": all_logs
                    }, f, ensure_ascii=False, indent=2)
            else:
                # 导出为文本格式
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"日志导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for log_file in log_files:
                        f.write(f"文件: {log_file}\n")
                        f.write("-" * 80 + "\n")
                        lines = self.read_log_file(log_file)
                        f.writelines(lines)
                        f.write("\n\n")
            
            print(f"日志导出成功: {output_file}")
            return True
        except Exception as e:
            print(f"导出日志失败: {e}")
            return False
    
    def clear_logs(self) -> bool:
        """
        清空所有日志
        
        Returns:
            是否成功
        """
        try:
            log_dir = Path(self.log_dir)
            if not log_dir.exists():
                return True
            
            # 删除所有日志文件
            for file in log_dir.glob("*.log"):
                file.unlink()
            
            # 清空操作历史
            if logger_manager.operation_logger:
                logger_manager.operation_logger.clear_history()
            
            print("日志已清空")
            return True
        except Exception as e:
            print(f"清空日志失败: {e}")
            return False
    
    def print_summary(self):
        """打印日志摘要"""
        print("\n" + "=" * 80)
        print("日志摘要")
        print("=" * 80)
        
        # 日志文件信息
        log_files = self.get_log_files()
        print(f"\n日志目录: {self.log_dir}")
        print(f"日志文件数量: {len(log_files)}")
        
        if log_files:
            total_size = sum(os.path.getsize(f) for f in log_files)
            print(f"总大小: {total_size / 1024:.2f} KB")
            
            print("\n日志文件列表:")
            for log_file in log_files:
                size = os.path.getsize(log_file)
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                print(f"  - {os.path.basename(log_file)} ({size / 1024:.2f} KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # 操作历史统计
        operations = self.get_operation_history()
        print(f"\n操作历史记录数: {len(operations)}")
        
        if operations:
            # 统计操作类型
            operation_types = {}
            for op in operations:
                op_type = op.get('operation_type', 'unknown')
                operation_types[op_type] = operation_types.get(op_type, 0) + 1
            
            print("\n操作类型统计:")
            for op_type, count in sorted(operation_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {op_type}: {count} 次")
        
        # 性能统计
        stats = self.get_performance_statistics()
        print(f"\n性能监控操作数: {len(stats)}")
        
        if stats:
            print("\n操作性能统计:")
            for op_name, stat in list(stats.items())[:5]:  # 只显示前5个
                print(f"  - {op_name}:")
                print(f"    执行次数: {stat.get('count', 0)}")
                print(f"    平均耗时: {stat.get('avg_time', 0):.3f} 秒")
                print(f"    最小耗时: {stat.get('min_time', 0):.3f} 秒")
                print(f"    最大耗时: {stat.get('max_time', 0):.3f} 秒")
        
        print("\n" + "=" * 80)


# 便捷函数
def view_logs():
    """查看日志（命令行工具）"""
    viewer = LogViewer()
    viewer.print_summary()


def export_logs_to_file(output_file: str, file_type: str = "txt"):
    """导出日志到文件"""
    viewer = LogViewer()
    viewer.export_logs(output_file, file_type)


def search_logs_in_file(file_path: str, keyword: str):
    """在日志文件中搜索"""
    viewer = LogViewer()
    results = viewer.search_logs(file_path, keyword)
    
    print(f"\n在 {file_path} 中搜索 '{keyword}' 的结果:")
    print("=" * 80)
    for line in results:
        print(line.rstrip())
    print("=" * 80)
    print(f"共找到 {len(results)} 条匹配记录")


# 命令行使用示例
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ADBTools 日志查看器")
    parser.add_argument("--view", action="store_true", help="查看日志摘要")
    parser.add_argument("--export", type=str, help="导出日志到文件")
    parser.add_argument("--type", type=str, choices=["txt", "json"], default="txt", help="导出文件类型")
    parser.add_argument("--search", type=str, help="搜索关键词")
    parser.add_argument("--file", type=str, help="要搜索的日志文件")
    
    args = parser.parse_args()
    
    if args.view:
        view_logs()
    elif args.export:
        export_logs_to_file(args.export, args.type)
    elif args.search and args.file:
        search_logs_in_file(args.file, args.search)
    else:
        parser.print_help()