# Flet 版本 ADBTools 开发指南

本项目基于 Flet 框架构建，采用了“单页应用”架构。所有的页面切换都是通过动态替换 `main_container.content` 来实现的。

## 1. 如何添加一个新页面 (侧边栏菜单)

如果你想在左侧导航栏增加一个新类目（例如：“性能监控”）：

1.  **修改侧边栏定义**：
    在 `main_flet.py` 的 `setup_ui` 方法中找到 `self.sidebar` 定义，在 `destinations` 列表中增加一项：
    ```python
    ft.NavigationRailDestination(icon=ft.Icons.MONITOR_HEART, label="性能监控"),
    ```

2.  **绑定切换逻辑**：
    在 `on_nav_change` 方法中增加索引判断，并调用对应的渲染方法：
    ```python
    elif idx == 8: self.show_performance_monitor()
    ```

3.  **创建页面渲染方法**：
    模仿其他 `show_xxx` 方法编写你的页面布局：
    ```python
    def show_performance_monitor(self):
        self.main_container.content = ft.Column([
            ft.Text("性能监控", size=20, weight="bold"),
            self.create_action_button("获取内存占用", ft.Icons.MEMORY, self.get_mem_info),
        ], scroll=ft.ScrollMode.AUTO)
        self.page.update()
    ```

---

## 2. 如何添加一个新按钮

推荐使用封装好的 `create_action_button` 方法，它能保证按钮样式统一。

- **语法**：`self.create_action_button(文字, 图标, 点击回调函数, 颜色(可选))`
- **图标**：使用 `ft.Icons.XXX` 形式。
- **示例**：
    ```python
    ft.Row([
        self.create_action_button("我的新功能", ft.Icons.AUTO_AWESOME, self.my_callback),
    ], spacing=10)
    ```

---

## 3. 如何编写功能逻辑 (ADB 指令)

**注意：所有的 ADB 指令必须在子线程中运行，以防界面卡死。**

### 方案 A：简单指令 (使用 `run_generic_cmd`)
如果你只需要运行一个命令并查看输出：
```python
def my_callback(self, _):
    self.run_generic_cmd("shell getprop ro.serialno")
```

### 方案 B：复杂逻辑 (手动开启线程)
如果你需要处理输出结果或执行多步操作：
```python
def get_mem_info(self, _):
    if not self.check_device(): return
    self.log("正在获取内存信息...")
    
    def task():
        # 调用底层工具类
        res = adb_utils.run_adb_command("shell dumpsys meminfo", self.selected_device)
        if res.returncode == 0:
            self.log(res.stdout) # 结果输出到控制台
        else:
            self.log(f"执行失败: {res.stderr}")
            
    threading.Thread(target=task).start()
```

---

## 4. 关键工具方法说明

| 方法名 | 说明 |
| :--- | :--- |
| `self.log(msg)` | 在底部的黑色控制台打印带时间戳的绿色日志。 |
| `self.check_device()` | 检查是否已选中设备，若未选中会弹出气泡提醒并返回 `False`。 |
| `self.run_generic_cmd(cmd)` | 自动在子线程运行 ADB 命令并将结果输出到控制台。 |
| `adb_utils.run_adb_command(cmd, device)` | 底层执行核心，位于 `adb_utils.py`。 |
| `self.connection_mode` | 当前模式 (`"u2"` 或 `"adb"`)。 |
| `self.d` | U2 模式下的 `uiautomator2` 实例对象。 |

## 5. UI 布局提示
- **间距**：`ft.Row` 或 `ft.Column` 的 `spacing` 属性控制子元素间距。
- **对齐**：使用 `alignment=ft.MainAxisAlignment.CENTER` 等属性。
- **分割线**：使用 `ft.Divider()`。
- **滚动**：容器通常设置 `scroll=ft.ScrollMode.AUTO`。
