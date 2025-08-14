from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import json
import os
import base64
from datetime import datetime
from typing import Optional, List
import uvicorn
from pathlib import Path

app = FastAPI(title="ExamAssistant Web Display", version="1.0.0")

# 数据存储路径
DATA_DIR = Path("web_data")
RESULTS_FILE = DATA_DIR / "results.json"
IMAGES_DIR = DATA_DIR / "images"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/web_data", StaticFiles(directory="web_data"), name="web_data")
templates = Jinja2Templates(directory="templates")

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
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载结果文件失败: {e}")
            return []
    return []

def save_results(results: List[dict]):
    """保存分析结果到文件"""
    try:
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存结果文件失败: {e}")

def generate_id() -> str:
    """生成唯一ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/results")
async def get_results():
    """获取所有分析结果"""
    results = load_results()
    return JSONResponse(content={"results": results})

@app.get("/api/results/latest")
async def get_latest_result():
    """获取最新的分析结果"""
    results = load_results()
    if results:
        return JSONResponse(content={"result": results[-1]})
    return JSONResponse(content={"result": None})

@app.post("/api/screenshot")
async def receive_screenshot(data: ScreenshotData):
    """接收截图数据和分析结果"""
    try:
        # 生成文件名和ID
        result_id = generate_id()
        timestamp = data.timestamp or datetime.now().isoformat()
        image_filename = f"screenshot_{result_id}.png"
        image_path = IMAGES_DIR / image_filename
        
        # 保存图片
        image_data = base64.b64decode(data.image_base64)
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        # 创建结果记录
        result = {
            "id": result_id,
            "type": "screenshot",
            "content": None,
            "image_path": f"images/{image_filename}",
            "analysis": data.analysis,
            "timestamp": timestamp
        }
        
        # 保存到结果文件
        results = load_results()
        results.append(result)
        save_results(results)
        
        return JSONResponse(content={"status": "success", "id": result_id})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理截图数据失败: {str(e)}")

@app.post("/api/clipboard")
async def receive_clipboard(data: ClipboardData):
    """接收剪贴板数据和分析结果"""
    try:
        # 生成ID
        result_id = generate_id()
        timestamp = data.timestamp or datetime.now().isoformat()
        
        # 创建结果记录
        result = {
            "id": result_id,
            "type": "clipboard",
            "content": data.text,
            "image_path": None,
            "analysis": data.analysis,
            "timestamp": timestamp
        }
        
        # 保存到结果文件
        results = load_results()
        results.append(result)
        save_results(results)
        
        return JSONResponse(content={"status": "success", "id": result_id})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理剪贴板数据失败: {str(e)}")

@app.delete("/api/results/{result_id}")
async def delete_result(result_id: str):
    """删除指定的分析结果"""
    try:
        results = load_results()
        original_count = len(results)
        
        # 找到并删除结果
        results = [r for r in results if r["id"] != result_id]
        
        if len(results) < original_count:
            save_results(results)
            return JSONResponse(content={"status": "success", "message": "结果已删除"})
        else:
            raise HTTPException(status_code=404, detail="未找到指定的结果")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除结果失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(content={"status": "healthy", "service": "ExamAssistant Web Display"})

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动Web服务器"""
    print(f"启动ExamAssistant Web服务器: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_server()