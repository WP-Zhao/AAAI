import pyperclip
from typing import Optional

class ClipboardManager:
    def __init__(self):
        self.last_content = ""
    
    def get_clipboard_content(self) -> Optional[str]:
        """获取剪贴板内容"""
        try:
            content = pyperclip.paste()
            if content:
                self.last_content = content
                print(f"获取剪贴板内容: {content[:100]}{'...' if len(content) > 100 else ''}")
                return content
            else:
                print("剪贴板为空")
                return None
        except Exception as e:
            print(f"获取剪贴板内容失败: {str(e)}")
            return None
    
    def set_clipboard_content(self, content: str) -> bool:
        """设置剪贴板内容"""
        try:
            pyperclip.copy(content)
            print(f"已设置剪贴板内容: {content[:100]}{'...' if len(content) > 100 else ''}")
            return True
        except Exception as e:
            print(f"设置剪贴板内容失败: {str(e)}")
            return False
    
    def clear_clipboard(self) -> bool:
        """清空剪贴板"""
        try:
            pyperclip.copy("")
            print("剪贴板已清空")
            return True
        except Exception as e:
            print(f"清空剪贴板失败: {str(e)}")
            return False
    
    def get_last_content(self) -> str:
        """获取最后一次获取的剪贴板内容"""
        return self.last_content
    
    def is_clipboard_empty(self) -> bool:
        """检查剪贴板是否为空"""
        try:
            content = pyperclip.paste()
            return not content or content.strip() == ""
        except Exception as e:
            print(f"检查剪贴板状态失败: {str(e)}")
            return True