import json
import os
import sys
import time
import signal
import threading
import logging
from datetime import datetime
from keyboard_listener import KeyboardListener
from screenshot import ScreenshotManager
from clipboard_manager import ClipboardManager
from email_sender import EmailSender
from llm_manager import LLMManager
from web_server import start_server

# 自定义日志格式化器，支持彩色输出
class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 获取原始消息
        message = super().format(record)
        
        # 根据日志级别添加颜色
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            # 只对特定的消息添加颜色，保持输出的美观
            if any(symbol in message for symbol in ['✓', '✗', '⚠']):
                return f"{color}{message}{reset}"
            elif record.levelname in ['ERROR', 'WARNING']:
                return f"{color}{message}{reset}"
        
        return message

# 配置日志系统
def setup_logging():
    """配置日志系统，详细日志保存到文件，控制台显示优美格式"""
    # 创建logs目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成日志文件名（包含时间戳）
    log_filename = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_format = '%(message)s'  # 控制台使用简化格式
    
    # 创建文件处理器（详细日志）
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # 创建控制台处理器（显示INFO及以上级别，使用彩色格式）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter(console_format))
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler]
    )
    
    # 创建应用专用日志器
    logger = logging.getLogger('ScreenCaptureApp')
    # 只在文件中记录初始化信息
    logger.debug(f"日志系统初始化完成，日志文件: {log_filename}")
    return logger

# 初始化日志系统
logger = setup_logging()

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
        self.logger = logging.getLogger('ScreenCaptureApp')
        self.logger.debug("ScreenCaptureApp实例初始化完成")
        
    def load_config(self, config_path="config.json"):
        """加载配置文件"""
        self.logger.debug(f"开始加载配置文件: {config_path}")
        try:
            if not os.path.exists(config_path):
                self.logger.error(f"配置文件不存在: {config_path}")
                self.logger.error(f"配置文件不存在: {config_path}")
                return False
                
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.logger.debug("配置文件加载成功")
            self.logger.debug(f"配置内容: {json.dumps(self.config, ensure_ascii=False, indent=2)}")
            self.logger.info("配置文件加载成功")
            return True
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}", exc_info=True)
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return False
    
    def initialize_components(self):
        """初始化各个组件"""
        self.logger.info("\n正在初始化组件...")
        self.logger.info("-" * 40)
        
        try:
            # 初始化截图管理器
            self.logger.info("[1/6] 初始化截图管理器... ✓ 成功")
            self.screenshot_manager = ScreenshotManager(self.config)
            
            # 初始化剪贴板管理器
            self.logger.info("[2/6] 初始化剪贴板管理器... ✓ 成功")
            self.clipboard_manager = ClipboardManager()
            
            # 初始化邮件发送器
            self.logger.info("[3/6] 初始化邮件发送器... ✓ 成功")
            self.email_sender = EmailSender(self.config)
            
            # 验证邮件配置（如果启用）
            if self.config.get('email', {}).get('enabled', True):
                self.logger.info("[4/6] 验证邮件配置...")
                if not self.email_sender.validate_config():
                    self.logger.error("✗ 失败")
                    self.logger.error("    邮件配置验证失败，请检查config.json文件")
                    return False
                self.logger.info("✓ 成功")
            else:
                self.logger.info("[4/6] 邮件功能已禁用，跳过验证")
            
            # 初始化LLM管理器
            self.logger.info("[5/6] 初始化LLM管理器... ✓ 成功")
            self.llm_manager = LLMManager(self.config)
            
            # 检查LLM可用性
            self.logger.info("[6/6] 检查LLM服务可用性...")
            llm_status = self.check_llm_availability()
            if llm_status:
                self.logger.info("✓ 可用")
            else:
                self.logger.warning("⚠ 不可用")
                self.logger.warning("    LLM服务不可用，将跳过AI分析功能")
                self.logger.warning("    请检查Ollama服务是否启动或API配置是否正确")
            
            # 初始化键盘监听器
            self.keyboard_listener = KeyboardListener(self.config)
            self.keyboard_listener.set_callbacks(
                self.on_screenshot_trigger,
                self.on_clipboard_trigger
            )
            
            # 启动Web服务（如果启用）
            web_service_config = self.config.get('web_service', {})
            if web_service_config.get('enabled', True):
                self.logger.info("[7/7] 启动Web服务...")
                self.logger.debug("Web服务已启用，开始启动")
                try:
                    self.start_web_service()
                    self.logger.info("✓ 成功")
                    self.logger.debug("Web服务启动成功")
                except Exception as e:
                    self.logger.error("✗ 失败")
                    self.logger.error(f"Web服务启动失败: {str(e)}", exc_info=True)
                    self.logger.error(f"    Web服务启动失败: {str(e)}")
                    return False
            else:
                self.logger.info("[7/7] Web服务已禁用，跳过启动")
                self.logger.debug("Web服务已禁用，跳过启动")
            
            self.logger.info("-" * 40)
            self.logger.info("所有组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ 失败")
            self.logger.error(f"组件初始化失败: {str(e)}")
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
            self.logger.error(f"    LLM可用性检查失败: {str(e)}")
            return False
    
    def start_web_service(self):
        """启动Web服务"""
        self.logger.debug("开始启动Web服务")
        try:
            web_config = self.config.get('web_service', {})
            host = web_config.get('host', '0.0.0.0')
            port = web_config.get('port', 8000)
            
            self.logger.debug(f"Web服务配置 - Host: {host}, Port: {port}")
            
            # 检查端口是否已被占用
            import socket
            self.logger.debug(f"检查端口 {port} 是否可用")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        self.logger.warning(f"Web服务端口 {port} 已被占用，跳过启动")
                        self.logger.warning(f"Web服务端口 {port} 已被占用，跳过启动")
                        return
                    else:
                        self.logger.debug(f"端口 {port} 可用")
            except Exception as e:
                self.logger.debug(f"端口检查异常: {str(e)}")
            
            # 在单独线程中启动Web服务
            self.logger.debug("创建Web服务线程")
            self.web_server_thread = threading.Thread(
                target=self._web_server_wrapper,
                args=(host, port),
                daemon=True,
                name="WebServerThread"
            )
            self.web_server_thread.start()
            self.logger.debug(f"Web服务线程已启动，线程ID: {self.web_server_thread.ident}")
            
            # 等待一小段时间，检查线程是否正常启动
            time.sleep(0.5)
            if self.web_server_thread.is_alive():
                self.logger.debug("Web服务线程运行正常")
            else:
                self.logger.error("Web服务线程启动后立即退出")
            
        except Exception as e:
            self.logger.error(f"Web服务启动失败: {str(e)}", exc_info=True)
            self.logger.error(f"Web服务启动失败: {str(e)}")
            raise
    
    def _web_server_wrapper(self, host: str, port: int):
        """Web服务器包装函数，用于捕获启动过程中的异常"""
        try:
            self.logger.debug(f"Web服务器线程开始执行，准备启动服务器 {host}:{port}")
            start_server(host, port)
        except Exception as e:
            self.logger.error(f"Web服务器线程执行失败: {str(e)}", exc_info=True)
            self.logger.error(f"Web服务器启动异常: {str(e)}")
            raise
    
    def on_screenshot_trigger(self):
        """截图触发回调函数"""
        self.logger.info("检测到截图触发信号...")
        
        # 截取屏幕
        screenshot_path = self.screenshot_manager.take_screenshot()
        
        if screenshot_path:
            # 如果LLM可用，先进行AI分析
            llm_analysis = None
            if self.llm_manager.is_enabled():
                self.logger.info("正在进行AI图像分析...")
                llm_analysis = self.llm_manager.process_image(screenshot_path)
                if llm_analysis:
                    self.logger.info("AI分析完成")
                else:
                    self.logger.warning("AI分析失败")
            
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
                        self.logger.info("截图数据已发送到Web服务")
                except Exception as e:
                    self.logger.error(f"发送截图到Web服务失败: {e}")
            
            # 发送截图邮件（如果启用）
            if self.config.get('email', {}).get('enabled', True):
                success = self.email_sender.send_screenshot_email(screenshot_path)
                if success:
                    self.logger.info("截图邮件发送成功")
                else:
                    self.logger.error("截图邮件发送失败")
            
            # 清理旧截图
            self.screenshot_manager.cleanup_old_screenshots()
        else:
            self.logger.error("截图失败")
    
    def on_clipboard_trigger(self):
        """剪贴板触发回调函数"""
        self.logger.info("检测到剪贴板触发信号...")
        
        # 获取剪贴板内容
        clipboard_content = self.clipboard_manager.get_clipboard_content()
        
        if clipboard_content:
            # 如果LLM可用，先进行AI分析
            llm_analysis = None
            if self.llm_manager.is_enabled():
                self.logger.info("正在进行AI文本分析...")
                llm_analysis = self.llm_manager.process_text(clipboard_content)
                if llm_analysis:
                    self.logger.info("AI分析完成")
                else:
                    self.logger.warning("AI分析失败")
            
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
                        self.logger.info("剪贴板数据已发送到Web服务")
                except Exception as e:
                    self.logger.error(f"发送剪贴板到Web服务失败: {e}")
            
            # 发送剪贴板邮件（如果启用）
            if self.config.get('email', {}).get('enabled', True):
                success = self.email_sender.send_clipboard_email(clipboard_content)
                if success:
                    self.logger.info("剪贴板邮件发送成功")
                else:
                    self.logger.error("剪贴板邮件发送失败")
        else:
            self.logger.warning("剪贴板内容为空")
    
    def start(self):
        """启动应用程序"""
        # 显示大型ASCII艺术logo
        logo = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     █████╗  █████╗  █████╗ ██╗                                             ║
║    ██╔══██╗██╔══██╗██╔══██╗██║                                             ║
║    ███████║███████║███████║██║                                             ║
║    ██╔══██║██╔══██║██╔══██║██║                                             ║
║    ██║  ██║██║  ██║██║  ██║██║                                             ║
║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝                                             ║
║                                                                              ║
║           Another AI Assistant for Interview (AAAI)                         ║
║                     智能面试助手 - 屏幕截图与分析工具                          ║
║                                                                              ║
║    🎯 功能特性:                                                               ║
║       • 智能截图分析 - AI驱动的图像理解                                        ║
║       • 剪贴板监控 - 自动文本分析与处理                                        ║
║       • Web界面管理 - 实时查看分析结果                                         ║
║       • 邮件通知 - 自动发送分析报告                                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self.logger.info(logo)
        
        # 加载配置
        if not self.load_config():
            return False
        
        # 初始化组件
        if not self.initialize_components():
            return False
        
        # 发送测试邮件（如果启用）
        if self.config.get('email', {}).get('enabled', True):
            self.logger.info("\n📧 正在发送测试邮件...")
            if self.email_sender.send_test_email():
                self.logger.info("✅ 测试邮件发送成功，邮件配置正常")
            else:
                self.logger.error("❌ 测试邮件发送失败，请检查邮件配置")
                response = input("是否继续运行程序？(y/n): ")
                if response.lower() != 'y':
                    return False
        else:
            self.logger.info("\n📧 邮件功能已禁用，跳过测试邮件")
        
        # 启动键盘监听
        self.keyboard_listener.start_listening()
        self.running = True
        
        # 显示操作说明
        operation_guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                              🚀 系统已就绪                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📖 操作指南:                                                                 ║
║                                                                              ║
║     ⌨️  截图功能:    连续按 3 次 Enter 键                                     ║
║     📋 剪贴板功能:   连续按 3 次 Shift 键                                     ║
║     🌐 Web界面:     http://localhost:8000                                   ║
║     📧 邮件通知:     自动发送分析结果                                          ║
║                                                                              ║
║  💡 提示: 按 Ctrl+C 可安全退出程序                                            ║
║                                                                              ║
║  🔄 程序正在后台运行，等待您的操作...                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self.logger.info(operation_guide)
        
        try:
            # 主循环
            while self.running:
                time.sleep(1)
                
                # 检查监听器状态
                if not self.keyboard_listener.is_running():
                    self.logger.warning("键盘监听器已停止，正在重启...")
                    self.keyboard_listener.start_listening()
                    
        except KeyboardInterrupt:
            self.logger.info("\n接收到退出信号...")
        except Exception as e:
            self.logger.error(f"\n程序运行出错: {str(e)}")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """停止应用程序"""
        self.logger.info("正在停止程序...")
        self.running = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop_listening()
        
        self.logger.info("程序已停止")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"\n接收到信号 {signum}，正在退出...")
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
        print("程序启动失败")  # 保留这个print，因为此时app可能没有logger
        sys.exit(1)

if __name__ == "__main__":
    main()
