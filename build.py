#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller打包脚本
用于将屏幕截图工具打包成独立的exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理目录: {dir_name}")
    
    # 清理.spec文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"已删除文件: {spec_file}")

def build_exe():
    """构建exe文件"""
    print("开始构建exe文件...")
    
    # PyInstaller命令参数
    cmd = [
        'pyinstaller',
        '--onefile',                    # 打包成单个exe文件
        '--windowed',                   # 无控制台窗口（后台运行）
        '--name=ScreenCapture',         # exe文件名
        '--icon=icon.ico',              # 图标文件（如果存在）
        '--add-data=config.json;.',     # 包含配置文件
        '--add-data=templates;templates',  # 包含模板文件夹
        '--add-data=static;static',     # 包含静态文件夹
        '--hidden-import=pynput.keyboard._win32',
        '--hidden-import=pynput.mouse._win32',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=fastapi',      # FastAPI Web框架
        '--hidden-import=uvicorn',      # ASGI服务器
        '--hidden-import=starlette',    # Starlette框架
        '--hidden-import=starlette.staticfiles',  # 静态文件支持
        '--hidden-import=starlette.templating',   # 模板支持
        '--hidden-import=jinja2',       # 模板引擎
        '--collect-all=pynput',
        '--collect-all=PIL',
        '--collect-all=pyperclip',
        '--collect-all=fastapi',        # 收集FastAPI所有模块
        '--collect-all=uvicorn',        # 收集uvicorn所有模块
        '--collect-all=starlette',      # 收集starlette所有模块
        'main.py'
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists('icon.ico'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
        print("未找到icon.ico文件，跳过图标设置")
    
    try:
        # 执行PyInstaller命令
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(result.stdout)
        
        # 复制配置文件和静态资源到dist目录
        dist_dir = Path('dist')
        if dist_dir.exists():
            # 复制配置文件
            config_src = Path('config.json')
            config_dst = dist_dir / 'config.json'
            
            if config_src.exists():
                shutil.copy2(config_src, config_dst)
                print(f"已复制配置文件到: {config_dst}")
            
            # 复制static文件夹
            static_src = Path('static')
            static_dst = dist_dir / 'static'
            
            if static_src.exists():
                if static_dst.exists():
                    shutil.rmtree(static_dst)
                shutil.copytree(static_src, static_dst)
                print(f"已复制静态文件夹到: {static_dst}")
            
            # 复制templates文件夹
            templates_src = Path('templates')
            templates_dst = dist_dir / 'templates'
            
            if templates_src.exists():
                if templates_dst.exists():
                    shutil.rmtree(templates_dst)
                shutil.copytree(templates_src, templates_dst)
                print(f"已复制模板文件夹到: {templates_dst}")
        
        print(f"\n构建完成！exe文件位于: {dist_dir / 'ScreenCapture.exe'}")
        print("配置文件和静态资源已自动复制到exe目录")
        
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    
    return True

def create_batch_file():
    """创建批处理文件用于快速打包"""
    batch_content = '''@echo off
echo 正在打包屏幕截图工具...
python build.py
echo.
echo 打包完成！按任意键退出...
pause > nul
'''
    
    with open('build.bat', 'w', encoding='gbk') as f:
        f.write(batch_content)
    
    print("已创建批处理文件: build.bat")

def main():
    print("=" * 50)
    print("屏幕截图工具 - PyInstaller打包脚本")
    print("=" * 50)
    
    # 检查是否安装了PyInstaller
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未找到PyInstaller，请先安装：pip install pyinstaller")
        return False
    
    # 清理旧的构建文件
    clean_build_dirs()
    
    # 构建exe
    success = build_exe()
    
    if success:
        # 创建批处理文件
        create_batch_file()
        
        print("\n" + "=" * 50)
        print("打包完成！")
        print("=" * 50)
        print("使用说明:")
        print("1. exe文件位于 dist/ 目录下")
        print("2. config.json、static和templates文件夹已自动复制")
        print("3. 双击exe文件即可运行")
        print("4. 程序将在后台运行，按Ctrl+C退出")
        print("\n快捷打包: 双击 build.bat 文件")
    
    return success

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)