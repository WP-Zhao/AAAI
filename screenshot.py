import os
import time
from datetime import datetime
from PIL import ImageGrab
from typing import Dict, Optional

class ScreenshotManager:
    def __init__(self, config: Dict):
        self.config = config
        self.save_path = config['screenshot']['save_path']
        self.image_format = config['screenshot']['image_format']
        
        # 确保截图保存目录存在
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """确保截图保存目录存在"""
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
            print(f"创建截图保存目录: {self.save_path}")
    
    def _generate_filename(self) -> str:
        """生成截图文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"screenshot_{timestamp}.{self.image_format.lower()}"
    
    def take_screenshot(self) -> Optional[str]:
        """截取全屏并保存"""
        try:
            # 截取全屏
            screenshot = ImageGrab.grab()
            
            # 生成文件名和完整路径
            filename = self._generate_filename()
            filepath = os.path.join(self.save_path, filename)
            
            # 保存截图
            screenshot.save(filepath, self.image_format)
            
            print(f"截图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return None
    
    def get_latest_screenshot(self) -> Optional[str]:
        """获取最新的截图文件路径"""
        try:
            if not os.path.exists(self.save_path):
                return None
            
            # 获取所有截图文件
            files = [f for f in os.listdir(self.save_path) 
                    if f.startswith('screenshot_') and f.lower().endswith(f'.{self.image_format.lower()}')]
            
            if not files:
                return None
            
            # 按修改时间排序，获取最新的
            files.sort(key=lambda x: os.path.getmtime(os.path.join(self.save_path, x)), reverse=True)
            latest_file = files[0]
            
            return os.path.join(self.save_path, latest_file)
            
        except Exception as e:
            print(f"获取最新截图失败: {str(e)}")
            return None
    
    def cleanup_old_screenshots(self, keep_count: int = 10):
        """清理旧的截图文件，只保留最新的几个"""
        try:
            if not os.path.exists(self.save_path):
                return
            
            # 获取所有截图文件
            files = [f for f in os.listdir(self.save_path) 
                    if f.startswith('screenshot_') and f.lower().endswith(f'.{self.image_format.lower()}')]
            
            if len(files) <= keep_count:
                return
            
            # 按修改时间排序
            files.sort(key=lambda x: os.path.getmtime(os.path.join(self.save_path, x)), reverse=True)
            
            # 删除多余的文件
            files_to_delete = files[keep_count:]
            for file in files_to_delete:
                filepath = os.path.join(self.save_path, file)
                os.remove(filepath)
                print(f"删除旧截图: {filepath}")
                
        except Exception as e:
            print(f"清理截图失败: {str(e)}")