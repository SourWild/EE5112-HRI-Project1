#!/usr/bin/env python3
"""
下载 Mistral-7B-Instruct GGUF 模型的脚本
"""
from huggingface_hub import hf_hub_download
import os

def download_mistral_model():
    """下载 Mistral-7B-Instruct Q4_K_M GGUF 模型"""
    
    # 确保 models 目录存在
    os.makedirs("models", exist_ok=True)
    
    print("开始下载 Mistral-7B-Instruct Q4_K_M GGUF 模型...")
    print("文件大小约 4.1GB，请耐心等待...")
    
    try:
        # 从 Hugging Face Hub 下载模型
        model_path = hf_hub_download(
            repo_id="TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
            filename="mistral-7b-instruct-v0.1.Q4_K_M.gguf",
            local_dir="models",
            local_dir_use_symlinks=False
        )
        
        print(f"✅ 模型下载成功！")
        print(f"📁 文件位置: {model_path}")
        print(f"📊 文件大小: {os.path.getsize(model_path) / (1024**3):.2f} GB")
        
        return model_path
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None

if __name__ == "__main__":
    download_mistral_model()