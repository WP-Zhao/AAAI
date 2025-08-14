# Another AI Assistant for Interview (AAAI)

一个基于AI的智能面试/考试辅助工具，支持屏幕截图分析、剪贴板内容处理和多种大语言模型服务。

## 🌟 功能特性

### 核心功能
- **智能截图分析**: 连续按Enter键触发屏幕截图，AI自动分析图片内容
- **剪贴板智能处理**: 连续按Shift键发送剪贴板文本内容进行AI分析
- **多模型支持**: 支持Ollama、OpenAI、Claude、豆包、千问等多种LLM服务
- **实时Web界面**: 提供美观的Web界面实时查看分析结果
- **邮件通知**: 可将分析结果通过邮件发送
- **历史记录**: 自动保存所有分析结果和截图

### 技术特点
- **键盘监听**: 基于pynput的全局键盘监听
- **多线程处理**: 异步处理截图和AI分析任务
- **RESTful API**: 基于FastAPI的现代Web服务
- **配置灵活**: 支持多种配置选项和服务提供商

## 📋 系统要求

- Python 3.13+
- Windows 操作系统
- 网络连接（用于AI服务调用）

## 🚀 快速开始

### 1. 安装依赖

使用uv（推荐）:
```bash
# 安装uv（如果尚未安装，或者github搜索uv）
pip install uv

# 安装项目依赖
uv sync
```

或使用pip:
```bash
pip install -r requirements.txt
```

### 2. 配置设置

⚠️ **重要安全提醒**: 配置文件包含敏感信息，请务必妥善保管！

复制配置文件模板：
```bash
cp config_example.json config.json
```

编辑 `config.json` 文件，配置你的服务：

```json
{
    "email": {
        "enabled": true,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "sender_password": "your-app-password",
        "receiver_email": "receiver@gmail.com"
    },
    "llm": {
        "enabled": true,
        "vision_model": {
            "provider": "ollama",
            "model": "llava:latest",
            "prompt": "请分析这张图片中的内容，特别是如果这是一道题目，请提供详细的解答。"
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "timeout": 1800
        }
    }
}
```

### 3. 启动服务

使用uv运行：
```bash
uv run python main.py
```

或直接运行：
```bash
python main.py
```

### 4. 访问Web界面

打开浏览器访问：http://localhost:8000

## 📖 使用方法

### 截图分析
1. 确保程序正在运行
2. 在任意界面连续按 **3次Enter键**
3. 程序自动截图并进行AI分析
4. 在Web界面查看分析结果

### 剪贴板分析
1. 复制需要分析的文本内容
2. 连续按 **3次Shift键**
3. 程序自动获取剪贴板内容并进行AI分析
4. 在Web界面查看分析结果

### Web界面功能
- **实时显示**: 自动刷新显示最新分析结果
- **历史记录**: 查看所有历史分析记录
- **结果管理**: 删除不需要的分析结果
- **状态监控**: 实时显示服务连接状态

## ⚙️ 配置说明

### 邮件配置
```json
"email": {
    "enabled": true,              // 是否启用邮件功能
    "smtp_server": "smtp.gmail.com", // SMTP服务器
    "smtp_port": 587,             // SMTP端口
    "sender_email": "your@email.com", // 发送者邮箱
    "sender_password": "password", // 邮箱密码或应用密码
    "receiver_email": "to@email.com" // 接收者邮箱
}
```

### LLM服务配置

#### Ollama（本地部署）
```json
"llm": {
    "vision_model": {
        "provider": "ollama",
        "model": "llava:latest"
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "timeout": 1800
    }
}
```

#### OpenAI
```json
"llm": {
    "vision_model": {
        "provider": "openai",
        "model": "gpt-4-vision-preview"
    },
    "openai": {
        "api_key": "your-openai-api-key",
        "base_url": "https://api.openai.com/v1"
    }
}
```

#### Claude
```json
"llm": {
    "vision_model": {
        "provider": "claude",
        "model": "claude-3-sonnet-20240229"
    },
    "claude": {
        "api_key": "your-claude-api-key"
    }
}
```

### 热键配置
```json
"hotkeys": {
    "screenshot_trigger": "enter",  // 截图触发键
    "clipboard_trigger": "shift",   // 剪贴板触发键
    "trigger_count": 3,             // 触发次数
    "trigger_timeout": 2.0          // 触发超时时间（秒）
}
```

### Web服务配置
```json
"web_service": {
    "enabled": true,        // 是否启用Web服务
    "host": "0.0.0.0",     // 监听地址
    "port": 8000,          // 监听端口
    "max_results": 100     // 最大保存结果数
}
```

## 🛠️ 开发说明

### 项目结构
```
├── main.py                 # 主程序入口
├── keyboard_listener.py    # 键盘监听模块
├── screenshot.py          # 截图管理模块
├── clipboard_manager.py   # 剪贴板管理模块
├── llm_manager.py         # LLM服务管理模块
├── email_sender.py        # 邮件发送模块
├── web_server.py          # Web服务模块
├── templates/             # HTML模板目录
│   └── index.html        # 主页面模板
├── static/               # 静态资源目录
│   ├── style.css        # 样式文件
│   └── script.js        # JavaScript文件
├── web_data/             # Web数据目录
│   ├── images/          # 截图存储目录
│   └── results.json     # 分析结果存储
├── screenshots/          # 本地截图存储目录
├── config.json          # 配置文件
└── requirements.txt     # 依赖列表
```

### API接口

- `GET /` - 主页面
- `GET /api/results` - 获取所有分析结果
- `GET /api/results/latest` - 获取最新分析结果
- `POST /api/screenshot` - 接收截图数据
- `POST /api/clipboard` - 接收剪贴板数据
- `DELETE /api/results/{id}` - 删除指定结果
- `GET /api/health` - 健康检查

## 🔧 故障排除

### 常见问题

1. **键盘监听不工作**
   - 确保程序以管理员权限运行
   - 检查是否有其他程序占用全局热键

2. **AI分析失败**
   - 检查网络连接
   - 验证API密钥是否正确
   - 确认模型名称是否正确

3. **Web服务无法访问**
   - 检查端口是否被占用
   - 确认防火墙设置
   - 验证配置文件中的host和port设置

4. **邮件发送失败**
   - 检查SMTP服务器设置
   - 确认邮箱密码或应用密码
   - 验证网络连接

### 日志查看
程序运行时会在控制台输出详细日志，包括：
- 组件初始化状态
- 键盘事件监听
- AI分析过程
- Web服务状态
- 错误信息

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 🔒 安全配置

### 重要安全提醒

⚠️ **配置文件安全**: 
- `config.json` 包含敏感信息（API密钥、邮箱密码等）
- 该文件已被 `.gitignore` 忽略，不会被提交到版本控制
- 请勿在公开场所分享此文件
- 建议定期更换API密钥和密码

## 📞 支持

如果你在使用过程中遇到问题，请：
1. 查看本README的故障排除部分
2. 检查控制台日志输出
3. 查看安全配置说明
4. 提交Issue描述问题详情

---

**注意**: 本工具仅供学习和研究使用，请遵守相关法律法规和学术诚信原则。使用前请仔细阅读安全配置说明。
