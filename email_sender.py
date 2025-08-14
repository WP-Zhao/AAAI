import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Dict, Optional
from datetime import datetime
from llm_manager import LLMManager

class EmailSender:
    def __init__(self, config: Dict):
        self.config = config
        self.email_config = config['email']
        self.llm_manager = LLMManager(config)
        
    def _create_connection(self):
        """创建SMTP连接"""
        try:
            server = smtplib.SMTP_SSL(
                self.email_config['smtp_server'], 
                self.email_config['smtp_port']
            )
            server.login(
                self.email_config['sender_email'], 
                self.email_config['sender_password']
            )
            return server
        except Exception as e:
            print(f"邮件服务器连接失败: {str(e)}")
            return None
    
    def send_screenshot_email(self, screenshot_path: str) -> bool:
        """发送截图邮件"""
        if not os.path.exists(screenshot_path):
            print(f"截图文件不存在: {screenshot_path}")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['receiver_email']
            msg['Subject'] = f"屏幕截图 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 使用LLM分析截图（如果启用）
            llm_analysis = ""
            if self.llm_manager.is_enabled():
                print("正在使用LLM分析截图...")
                analysis_result = self.llm_manager.process_image(screenshot_path)
                if analysis_result:
                    llm_analysis = f"\n\n=== LLM分析结果 ===\n{analysis_result}\n=== 分析结束 ==="
                    print("LLM截图分析完成")
                else:
                    print("LLM截图分析失败")
            
            # 添加邮件正文
            body = f"""自动截图邮件
            
截图时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
截图文件: {os.path.basename(screenshot_path)}{llm_analysis}
            
此邮件由屏幕截图工具自动发送。"""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加截图附件
            with open(screenshot_path, 'rb') as f:
                img_data = f.read()
                img = MIMEImage(img_data)
                img.add_header('Content-Disposition', 
                             f'attachment; filename="{os.path.basename(screenshot_path)}"')
                msg.attach(img)
            
            # 发送邮件
            server = self._create_connection()
            if server:
                server.send_message(msg)
                server.quit()
                print(f"截图邮件发送成功: {screenshot_path}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"发送截图邮件失败: {str(e)}")
            return False
    
    def send_clipboard_email(self, clipboard_content: str) -> bool:
        """发送剪贴板内容邮件"""
        if not clipboard_content or clipboard_content.strip() == "":
            print("剪贴板内容为空，无法发送邮件")
            return False
        
        try:
            # 使用LLM分析剪贴板内容（如果启用）
            email_content = clipboard_content
            if self.llm_manager.is_enabled():
                print("正在使用LLM分析剪贴板内容...")
                analysis_result = self.llm_manager.process_text(clipboard_content)
                if analysis_result:
                    email_content = f"""原始内容：
{clipboard_content}

=== LLM分析结果 ===
{analysis_result}
=== 分析结束 ==="""
                    print("LLM剪贴板分析完成")
                else:
                    print("LLM剪贴板分析失败")
            
            # 创建邮件
            msg = MIMEText(email_content, 'plain', 'utf-8')
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['receiver_email']
            msg['Subject'] = f"剪贴板内容 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 发送邮件
            server = self._create_connection()
            if server:
                server.send_message(msg)
                server.quit()
                print(f"剪贴板邮件发送成功，内容长度: {len(clipboard_content)} 字符")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"发送剪贴板邮件失败: {str(e)}")
            return False
    
    def send_test_email(self) -> bool:
        """发送测试邮件"""
        try:
            msg = MIMEText("这是一封测试邮件，用于验证邮件配置是否正确。", 'plain', 'utf-8')
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['receiver_email']
            msg['Subject'] = f"测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            server = self._create_connection()
            if server:
                server.send_message(msg)
                server.quit()
                print("测试邮件发送成功")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"发送测试邮件失败: {str(e)}")
            return False
    
    def validate_config(self) -> bool:
        """验证邮件配置"""
        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'receiver_email']
        
        for field in required_fields:
            if field not in self.email_config or not self.email_config[field]:
                print(f"邮件配置缺少必要字段: {field}")
                return False
        
        # 验证LLM配置（如果启用）
        if not self.llm_manager.validate_config():
            print("LLM配置验证失败")
            return False
        
        print("邮件配置验证通过")
        return True