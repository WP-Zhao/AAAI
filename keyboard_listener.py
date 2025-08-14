import time
from pynput import keyboard
from typing import Callable, Dict, List
import threading

class KeyboardListener:
    def __init__(self, config: Dict):
        self.config = config
        self.trigger_count = config['hotkeys']['trigger_count']
        self.trigger_timeout = config['hotkeys']['trigger_timeout']
        
        # 存储按键时间戳
        self.enter_times: List[float] = []
        self.shift_times: List[float] = []
        
        # 回调函数
        self.screenshot_callback: Callable = None
        self.clipboard_callback: Callable = None
        
        # 监听器
        self.listener = None
        self.running = False
        
    def set_callbacks(self, screenshot_callback: Callable, clipboard_callback: Callable):
        """设置回调函数"""
        self.screenshot_callback = screenshot_callback
        self.clipboard_callback = clipboard_callback
    
    def _clean_old_timestamps(self, timestamps: List[float]) -> List[float]:
        """清理超时的时间戳"""
        current_time = time.time()
        return [t for t in timestamps if current_time - t <= self.trigger_timeout]
    
    def _check_trigger(self, timestamps: List[float], callback: Callable):
        """检查是否触发条件"""
        if len(timestamps) >= self.trigger_count and callback:
            # 清空时间戳列表，避免重复触发
            timestamps.clear()
            # 在新线程中执行回调，避免阻塞监听器
            threading.Thread(target=callback, daemon=True).start()
    
    def _on_key_press(self, key):
        """按键按下事件处理"""
        current_time = time.time()
        
        try:
            if key == keyboard.Key.enter:
                # 清理旧的时间戳
                self.enter_times = self._clean_old_timestamps(self.enter_times)
                # 添加新的时间戳
                self.enter_times.append(current_time)
                # 检查是否触发截图
                self._check_trigger(self.enter_times, self.screenshot_callback)
                
            elif key == keyboard.Key.shift or key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                # 清理旧的时间戳
                self.shift_times = self._clean_old_timestamps(self.shift_times)
                # 添加新的时间戳
                self.shift_times.append(current_time)
                # 检查是否触发剪贴板发送
                self._check_trigger(self.shift_times, self.clipboard_callback)
                
        except AttributeError:
            # 处理特殊按键
            pass
    
    def start_listening(self):
        """开始监听键盘事件"""
        if self.running:
            return
            
        self.running = True
        self.listener = keyboard.Listener(on_press=self._on_key_press)
        self.listener.start()
        print("键盘监听已启动...")
        print(f"连续按{self.trigger_count}次Enter键进行截图")
        print(f"连续按{self.trigger_count}次Shift键发送剪贴板内容")
    
    def stop_listening(self):
        """停止监听键盘事件"""
        if self.listener and self.running:
            self.listener.stop()
            self.running = False
            print("键盘监听已停止")
    
    def is_running(self) -> bool:
        """检查监听器是否正在运行"""
        return self.running and self.listener and self.listener.running