from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import json
import os
import sys
import base64
from datetime import datetime
from typing import Optional, List
import uvicorn
from pathlib import Path
import logging

# 配置Web服务器日志
web_logger = logging.getLogger('WebServer')
web_logger.setLevel(logging.INFO)

def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
    web_logger.info(f"解析资源路径: {relative_path}")
    try:
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
        web_logger.info(f"检测到PyInstaller环境，基础路径: {base_path}")
    except AttributeError:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
        web_logger.info(f"开发环境，基础路径: {base_path}")
    
    full_path = os.path.join(base_path, relative_path)
    web_logger.info(f"完整资源路径: {full_path}")
    
    # 检查路径是否存在
    if os.path.exists(full_path):
        web_logger.info(f"资源路径存在: {full_path}")
    else:
        web_logger.warning(f"资源路径不存在: {full_path}")
    
    return full_path

web_logger.info("初始化FastAPI应用")
app = FastAPI(title="ExamAssistant Web Display", version="1.0.0")
web_logger.info("FastAPI应用创建成功")

# 数据存储路径
web_logger.info("设置数据存储路径")
DATA_DIR = Path("web_data")
RESULTS_FILE = DATA_DIR / "results.json"
IMAGES_DIR = DATA_DIR / "images"
web_logger.info(f"数据目录: {DATA_DIR}, 结果文件: {RESULTS_FILE}, 图片目录: {IMAGES_DIR}")

# 确保目录存在
web_logger.info("创建必要的目录")
try:
    DATA_DIR.mkdir(exist_ok=True)
    web_logger.info(f"数据目录创建成功: {DATA_DIR}")
    IMAGES_DIR.mkdir(exist_ok=True)
    web_logger.info(f"图片目录创建成功: {IMAGES_DIR}")
except Exception as e:
    web_logger.error(f"创建目录失败: {str(e)}", exc_info=True)
    raise

# 静态文件和模板 - 使用动态路径解析
web_logger.info("配置静态文件和模板目录")
static_dir = get_resource_path("static")
templates_dir = get_resource_path("templates")
web_data_dir = "web_data"  # 这个目录在运行时创建，不需要动态路径

web_logger.info(f"静态文件目录: {static_dir}")
web_logger.info(f"模板目录: {templates_dir}")
web_logger.info(f"Web数据目录: {web_data_dir}")

try:
    web_logger.info("挂载静态文件目录")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    web_logger.info("静态文件目录挂载成功")
    
    app.mount("/web_data", StaticFiles(directory=web_data_dir), name="web_data")
    web_logger.info("Web数据目录挂载成功")
    
    web_logger.info("初始化模板引擎")
    templates = Jinja2Templates(directory=templates_dir)
    web_logger.info("模板引擎初始化成功")
except Exception as e:
    web_logger.error(f"静态文件或模板配置失败: {str(e)}", exc_info=True)
    raise

class AnalysisResult(BaseModel):
    type: str  # "screenshot" or "clipboard"
    content: Optional[str] = None  # 剪贴板文本内容
    image_path: Optional[str] = None  # 截图文件路径
    analysis: str  # LLM分析结果
    timestamp: str
    id: str

class ScreenshotData(BaseModel):
    image_base64: str
    analysis: str
    timestamp: Optional[str] = None

class ClipboardData(BaseModel):
    text: str
    analysis: str
    timestamp: Optional[str] = None

def load_results() -> List[dict]:
    """加载存储的分析结果"""
    web_logger.info(f"尝试加载结果文件: {RESULTS_FILE}")
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
            web_logger.info(f"成功加载 {len(results)} 条结果")
            return results
        except json.JSONDecodeError as e:
            web_logger.error(f"结果文件JSON格式错误: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            web_logger.error(f"加载结果文件失败: {str(e)}", exc_info=True)
            return []
    else:
        web_logger.info("结果文件不存在，返回空列表")
        return []

def save_results(results: List[dict]):
    """保存分析结果到文件"""
    web_logger.info(f"尝试保存 {len(results)} 条结果到文件: {RESULTS_FILE}")
    try:
        # 确保目录存在
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        web_logger.info(f"成功保存结果文件: {RESULTS_FILE}")
    except PermissionError as e:
        web_logger.error(f"保存结果文件权限不足: {str(e)}", exc_info=True)
        raise
    except json.JSONEncodeError as e:
        web_logger.error(f"结果数据JSON序列化失败: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        web_logger.error(f"保存结果文件失败: {str(e)}", exc_info=True)
        raise

def generate_id() -> str:
    """生成唯一ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页 - 显示所有分析结果"""
    web_logger.info("收到主页访问请求")
    try:
        results = load_results()
        web_logger.info(f"加载了 {len(results)} 条分析结果")
        return templates.TemplateResponse("index.html", {"request": request, "results": results})
    except Exception as e:
        web_logger.error(f"主页加载失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"主页加载失败: {str(e)}")

@app.get("/api/results")
async def get_results():
    """获取所有分析结果"""
    web_logger.info("收到获取所有结果请求")
    try:
        results = load_results()
        web_logger.info(f"返回 {len(results)} 条结果")
        return JSONResponse(content={"results": results})
    except Exception as e:
        web_logger.error(f"获取结果失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")

@app.get("/api/results/latest")
async def get_latest_result():
    """获取最新的分析结果"""
    web_logger.info("收到获取最新结果请求")
    try:
        results = load_results()
        if results:
            web_logger.info(f"返回最新结果，ID: {results[-1].get('id', 'unknown')}")
            return JSONResponse(content={"result": results[-1]})
        else:
            web_logger.info("没有找到任何结果")
            return JSONResponse(content={"result": None})
    except Exception as e:
        web_logger.error(f"获取最新结果失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取最新结果失败: {str(e)}")

@app.post("/api/screenshot")
async def receive_screenshot(data: ScreenshotData):
    """接收截图数据和分析结果"""
    web_logger.info("收到截图数据请求")
    try:
        # 生成文件名和ID
        result_id = generate_id()
        web_logger.info(f"生成结果ID: {result_id}")
        timestamp = data.timestamp or datetime.now().isoformat()
        image_filename = f"screenshot_{result_id}.png"
        image_path = IMAGES_DIR / image_filename
        
        # 保存图片
        web_logger.info("开始保存图片")
        image_data = base64.b64decode(data.image_base64)
        with open(image_path, 'wb') as f:
            f.write(image_data)
        web_logger.info(f"图片保存成功: {image_path}")
        
        # 创建结果记录
        web_logger.info("创建分析结果对象")
        result = {
            "id": result_id,
            "type": "screenshot",
            "content": None,
            "image_path": f"images/{image_filename}",
            "analysis": data.analysis,
            "timestamp": timestamp
        }
        
        # 保存到结果文件
        web_logger.info("保存分析结果")
        results = load_results()
        results.append(result)
        save_results(results)
        web_logger.info(f"截图数据处理完成，ID: {result_id}")
        
        return JSONResponse(content={"status": "success", "id": result_id})
    
    except Exception as e:
        web_logger.error(f"处理截图数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理截图数据失败: {str(e)}")

@app.post("/api/clipboard")
async def receive_clipboard(data: ClipboardData):
    """接收剪贴板数据和分析结果"""
    web_logger.info("收到剪贴板数据请求")
    try:
        # 生成文件名和ID
        result_id = generate_id()
        web_logger.info(f"生成结果ID: {result_id}")
        timestamp = data.timestamp or datetime.now().isoformat()
        web_logger.info(f"剪贴板文本长度: {len(data.text) if data.text else 0}")
        
        # 创建结果记录
        web_logger.info("创建剪贴板分析结果对象")
        result = {
            "id": result_id,
            "timestamp": timestamp,
            "type": "clipboard",
            "content": data.text,
            "analysis": data.analysis,
            "image_path": None
        }
        
        # 保存到结果文件
        web_logger.info("保存剪贴板分析结果")
        results = load_results()
        results.append(result)
        save_results(results)
        web_logger.info(f"剪贴板数据处理完成，ID: {result_id}")
        
        return JSONResponse(content={"status": "success", "id": result_id})
    
    except Exception as e:
        web_logger.error(f"处理剪贴板数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理剪贴板数据失败: {str(e)}")

@app.delete("/api/results/{result_id}")
async def delete_result(result_id: str):
    """删除指定的分析结果"""
    web_logger.info(f"收到删除结果请求，ID: {result_id}")
    try:
        results = load_results()
        original_count = len(results)
        web_logger.info(f"当前共有 {original_count} 条结果")
        
        # 找到并删除结果
        results = [r for r in results if r["id"] != result_id]
        
        if len(results) < original_count:
            save_results(results)
            web_logger.info(f"成功删除结果 {result_id}，剩余 {len(results)} 条结果")
            return JSONResponse(content={"status": "success", "message": "结果已删除"})
        else:
            web_logger.warning(f"未找到要删除的结果 ID: {result_id}")
            raise HTTPException(status_code=404, detail="未找到指定的结果")
    
    except HTTPException:
        raise
    except Exception as e:
        web_logger.error(f"删除结果失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除结果失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(content={"status": "healthy", "service": "ExamAssistant Web Display"})

def start_server(host: str = "127.0.0.1", port: int = 8000):
    """启动Web服务器"""
    web_logger.info(f"准备启动Web服务器 - 主机: {host}, 端口: {port}")
    
    try:
        # 检查端口是否可用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host if host != '0.0.0.0' else 'localhost', port))
        sock.close()
        
        if result == 0:
            web_logger.warning(f"端口 {port} 已被占用")
        else:
            web_logger.info(f"端口 {port} 可用")
        
        web_logger.info("启动uvicorn服务器...")
        # 禁用uvicorn默认日志配置以避免PyInstaller打包环境下sys.stdout为None的问题
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            log_config=None,  # 禁用默认日志配置
            access_log=False  # 禁用访问日志以避免stdout问题
        )
        web_logger.info("Web服务器启动成功")
        
    except Exception as e:
        web_logger.error(f"Web服务器启动失败: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    start_server()