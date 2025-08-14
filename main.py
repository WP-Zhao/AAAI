import json
import os
import sys
import time
import signal
import threading
from keyboard_listener import KeyboardListener
from screenshot import ScreenshotManager
from clipboard_manager import ClipboardManager
from email_sender import EmailSender
from llm_manager import LLMManager
from web_server import start_server

class ScreenCaptureApp:
    def __init__(self):
        self.config = None
        self.keyboard_listener = None
        self.screenshot_manager = None
        self.clipboard_manager = None
        self.email_sender = None
        self.llm_manager = None
        self.web_server_thread = None
        self.running = False
        
    def load_config(self, config_path="config.json"):
        """加载配置文件"""
        try:
            if not os.path.exists(config_path):
                print(f"配置文件不存在: {config_path}")
                return False
                
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print("配置文件加载成功")
            return True
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return False
    
    def initialize_components(self):
        """初始化各个组件"""
        print("\n正在初始化组件...")
        print("-" * 40)
        
        try:
            # 初始化截图管理器
            print("[1/6] 初始化截图管理器...", end=" ")
            self.screenshot_manager = ScreenshotManager(self.config)
            print("✓ 成功")
            
            # 初始化剪贴板管理器
            print("[2/6] 初始化剪贴板管理器...", end=" ")
            self.clipboard_manager = ClipboardManager()
            print("✓ 成功")
            
            # 初始化邮件发送器
            print("[3/6] 初始化邮件发送器...", end=" ")
            self.email_sender = EmailSender(self.config)
            print("✓ 成功")
            
            # 验证邮件配置（如果启用）
            if self.config.get('email', {}).get('enabled', True):
                print("[4/6] 验证邮件配置...", end=" ")
                if not self.email_sender.validate_config():
                    print("✗ 失败")
                    print("    邮件配置验证失败，请检查config.json文件")
                    return False
                print("✓ 成功")
            else:
                print("[4/6] 邮件功能已禁用，跳过验证")
            
            # 初始化LLM管理器
            print("[5/6] 初始化LLM管理器...", end=" ")
            self.llm_manager = LLMManager(self.config)
            print("✓ 成功")
            
            # 检查LLM可用性
            print("[6/6] 检查LLM服务可用性...", end=" ")
            llm_status = self.check_llm_availability()
            if llm_status:
                print("✓ 可用")
            else:
                print("⚠ 不可用")
                print("    LLM服务不可用，将跳过AI分析功能")
                print("    请检查Ollama服务是否启动或API配置是否正确")
            
            # 初始化键盘监听器
            self.keyboard_listener = KeyboardListener(self.config)
            self.keyboard_listener.set_callbacks(
                self.on_screenshot_trigger,
                self.on_clipboard_trigger
            )
            
            # 启动Web服务（如果启用）
            if self.config.get('web_service', {}).get('enabled', True):
                print("[7/7] 启动Web服务...", end=" ")
                self.start_web_service()
                print("✓ 成功")
            
            print("-" * 40)
            print("所有组件初始化完成")
            return True
            
        except Exception as e:
            print(f"✗ 失败")
            print(f"组件初始化失败: {str(e)}")
            return False
    
    def check_llm_availability(self) -> bool:
        """检查LLM服务可用性"""
        try:
            if not self.llm_manager.is_enabled():
                return False
            
            # 验证LLM配置
            if not self.llm_manager.validate_config():
                return False
            
            # 检查LLM服务可用性
            return self.llm_manager.check_availability()
            
        except Exception as e:
            print(f"    LLM可用性检查失败: {str(e)}")
            return False
    
    def start_web_service(self):
        """启动Web服务"""
        try:
            web_config = self.config.get('web_service', {})
            host = web_config.get('host', '0.0.0.0')
            port = web_config.get('port', 8000)
            
            # 检查端口是否已被占用
            import socket
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        print(f"Web服务端口 {port} 已被占用，跳过启动")
                        return
            except Exception:
                pass
            
            # 在单独线程中启动Web服务
            self.web_server_thread = threading.Thread(
                target=start_server,
                args=(host, port),
                daemon=True
            )
            self.web_server_thread.start()
            
        except Exception as e:
            print(f"Web服务启动失败: {str(e)}")
            raise
    
    def on_screenshot_trigger(self):
        """截图触发回调函数"""
        print("检测到截图触发信号...")
        
        # 截取屏幕
        screenshot_path = self.screenshot_manager.take_screenshot()
        
        if screenshot_path:
            # 如果LLM可用，先进行AI分析
            llm_analysis = None
            if self.llm_manager.is_enabled():
                print("正在进行AI图像分析...")
                llm_analysis = self.llm_manager.process_image(screenshot_path)
                if llm_analysis:
                    print("AI分析完成")
                else:
                    print("AI分析失败")
            
            # 发送到Web服务（如果启用）
            if self.config.get('web_service', {}).get('enabled', True):
                try:
                    import requests
                    import base64
                    from datetime import datetime
                    
                    # 读取截图并转换为base64
                    with open(screenshot_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    # 发送到Web服务
                    web_config = self.config.get('web_service', {})
                    host = web_config.get('host', '0.0.0.0')
                    # 如果host是0.0.0.0，发送请求时使用localhost
                    request_host = 'localhost' if host == '0.0.0.0' else host
                    port = web_config.get('port', 8000)
                    
                    response = requests.post(
                        f"http://{request_host}:{port}/api/screenshot",
                        json={
                            "image_base64": image_data,
                            "analysis": llm_analysis,
                            "timestamp": datetime.now().isoformat()
                        },
                        timeout=5
                    )
                    if response.status_code == 200:
                        print("截图数据已发送到Web服务")
                except Exception as e:
                    print(f"发送截图到Web服务失败: {e}")
            
            # 发送截图邮件（如果启用）
            if self.config.get('email', {}).get('enabled', True):
                success = self.email_sender.send_screenshot_email(screenshot_path)
                if success:
                    print("截图邮件发送成功")
                else:
                    print("截图邮件发送失败")
            
            # 清理旧截图
            self.screenshot_manager.cleanup_old_screenshots()
        else:
            print("截图失败")
    
    def on_clipboard_trigger(self):
        """剪贴板触发回调函数"""
        print("检测到剪贴板触发信号...")
        
        # 获取剪贴板内容
        clipboard_content = self.clipboard_manager.get_clipboard_content()
        
        if clipboard_content:
            # 如果LLM可用，先进行AI分析
            llm_analysis = None
            if self.llm_manager.is_enabled():
                print("正在进行AI文本分析...")
                llm_analysis = self.llm_manager.process_text(clipboard_content)
                if llm_analysis:
                    print("AI分析完成")
                else:
                    print("AI分析失败")
            
            # 发送到Web服务（如果启用）
            if self.config.get('web_service', {}).get('enabled', True):
                try:
                    import requests
                    from datetime import datetime
                    
                    # 发送到Web服务
                    web_config = self.config.get('web_service', {})
                    host = web_config.get('host', '0.0.0.0')
                    # 如果host是0.0.0.0，发送请求时使用localhost
                    request_host = 'localhost' if host == '0.0.0.0' else host
                    port = web_config.get('port', 8000)
                    
                    response = requests.post(
                        f"http://{request_host}:{port}/api/clipboard",
                        json={
                            "text": clipboard_content,
                            "analysis": llm_analysis,
                            "timestamp": datetime.now().isoformat()
                        },
                        timeout=5
                    )
                    if response.status_code == 200:
                        print("剪贴板数据已发送到Web服务")
                except Exception as e:
                    print(f"发送剪贴板到Web服务失败: {e}")
            
            # 发送剪贴板邮件（如果启用）
            if self.config.get('email', {}).get('enabled', True):
                success = self.email_sender.send_clipboard_email(clipboard_content)
                if success:
                    print("剪贴板邮件发送成功")
                else:
                    print("剪贴板邮件发送失败")
        else:
            print("剪贴板内容为空")
    
    def start(self):
        """启动应用程序"""
        print("=" * 50)
        print("Windows 屏幕截图工具")
        print("=" * 50)
        
        # 加载配置
        if not self.load_config():
            return False
        
        # 初始化组件
        if not self.initialize_components():
            return False
        
        # 发送测试邮件（如果启用）
        if self.config.get('email', {}).get('enabled', True):
            print("\n正在发送测试邮件...")
            if self.email_sender.send_test_email():
                print("测试邮件发送成功，邮件配置正常")
            else:
                print("测试邮件发送失败，请检查邮件配置")
                response = input("是否继续运行程序？(y/n): ")
                if response.lower() != 'y':
                    return False
        else:
            print("\n邮件功能已禁用，跳过测试邮件")
        
        # 启动键盘监听
        self.keyboard_listener.start_listening()
        self.running = True
        
        print("\n程序已启动，正在后台运行...")
        print("按 Ctrl+C 退出程序")
        print("-" * 50)
        
        try:
            # 主循环
            while self.running:
                time.sleep(1)
                
                # 检查监听器状态
                if not self.keyboard_listener.is_running():
                    print("键盘监听器已停止，正在重启...")
                    self.keyboard_listener.start_listening()
                    
        except KeyboardInterrupt:
            print("\n接收到退出信号...")
        except Exception as e:
            print(f"\n程序运行出错: {str(e)}")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """停止应用程序"""
        print("正在停止程序...")
        self.running = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop_listening()
        
        print("程序已停止")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n接收到信号 {signum}，正在退出...")
        self.stop()
        sys.exit(0)

def main():
    # 创建应用实例
    app = ScreenCaptureApp()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGTERM, app.signal_handler)
    
    # 启动应用
    success = app.start()
    
    if not success:
        print("程序启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
