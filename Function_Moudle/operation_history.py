from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Dict, Any, Optional
from datetime import datetime


class OperationRecord:
    """操作记录类"""
    
    def __init__(self, operation_type: str, description: str, data: Optional[Dict[str, Any]] = None):
        self.operation_type = operation_type
        self.description = description
        self.data = data or {}
        self.timestamp = datetime.now()
        self.undoable = True  # 是否可撤销
        self.redoable = False  # 是否可重做
    
    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.description}"


class OperationHistoryManager(QObject):
    """操作历史管理器"""
    
    # 信号定义
    history_changed_signal = pyqtSignal()  # 历史记录变化信号
    can_undo_changed_signal = pyqtSignal(bool)  # 可撤销状态变化
    can_redo_changed_signal = pyqtSignal(bool)  # 可重做状态变化
    
    def __init__(self, max_history_size: int = 50):
        super().__init__()
        self.max_history_size = max_history_size
        self.history: List[OperationRecord] = []
        self.current_index = -1  # 当前操作索引
        self._can_undo = False
        self._can_redo = False
    
    def add_operation(self, operation_type: str, description: str, data: Optional[Dict[str, Any]] = None) -> None:
        """添加操作记录"""
        # 如果当前不在历史记录末尾，清除当前位置之后的记录
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # 创建操作记录
        record = OperationRecord(operation_type, description, data)
        self.history.append(record)
        
        # 如果超过最大历史记录数，删除最早的记录
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
        
        # 更新当前索引
        self.current_index = len(self.history) - 1
        
        # 更新状态
        self._update_status()
        
        # 发送信号
        self.history_changed_signal.emit()
    
    def undo(self) -> Optional[OperationRecord]:
        """撤销操作"""
        if self.can_undo():
            record = self.history[self.current_index]
            self.current_index -= 1
            self._update_status()
            self.history_changed_signal.emit()
            return record
        return None
    
    def redo(self) -> Optional[OperationRecord]:
        """重做操作"""
        if self.can_redo():
            self.current_index += 1
            record = self.history[self.current_index]
            self._update_status()
            self.history_changed_signal.emit()
            return record
        return None
    
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return self._can_undo
    
    def can_redo(self) -> bool:
        """是否可以重做"""
        return self._can_redo
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.history.clear()
        self.current_index = -1
        self._update_status()
        self.history_changed_signal.emit()
    
    def get_current_operation(self) -> Optional[OperationRecord]:
        """获取当前操作"""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index]
        return None
    
    def get_history_list(self) -> List[str]:
        """获取历史记录列表（用于显示）"""
        return [str(record) for record in self.history]
    
    def _update_status(self) -> None:
        """更新可撤销和可重做状态"""
        old_can_undo = self._can_undo
        old_can_redo = self._can_redo
        
        self._can_undo = self.current_index >= 0
        self._can_redo = self.current_index < len(self.history) - 1
        
        # 发送状态变化信号
        if self._can_undo != old_can_undo:
            self.can_undo_changed_signal.emit(self._can_undo)
        if self._can_redo != old_can_redo:
            self.can_redo_changed_signal.emit(self._can_redo)
