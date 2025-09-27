# EE5112 HCI Course Project - Large Language Models Exploration

## 项目概述

本项目是EE5112人机交互课程的综合性项目，包含四个主要任务，全面探索大语言模型(LLMs)和多模态大语言模型(MLLMs)的应用。项目涵盖了从基础对话系统到多模态AI助手的完整技术栈。

## 项目结构

```
cor-project1/
├── task1/                    # 商店接待员对话系统
│   ├── task1.py             # 主程序
│   ├── download_model.py    # 模型下载脚本
│   ├── Task1_Report.md      # 任务子报告
│   └── picture.pptx         # 演示图片
├── task2/                    # 本地对话系统比较
│   ├── chat_llama_Mistral-7B-Instruct.py
│   ├── chat_llama_Orca-Mini-3B.py
│   └── Task2_Report.md      # 任务报告
├── task4/                    # GUI界面设计
│   ├── chat_gui.py          # GUI主程序
│   ├── chat_backend.py      # 后端逻辑
│   └── Task4_Report.md      # 任务子报告
├── task5/                    # 多模态大语言模型
│   ├── llava_project/       # LLaVA项目
│   └── Task5_Report.md      # 任务子报告
├── models/                   # 模型文件存储
├── runs/                     # 运行日志
└── requirements.txt          # 项目依赖
```

## 任务详情

### Task 1: 商店接待员对话系统
- **目标**: 开发基于Mistral-7B-Instruct的商店接待员对话系统
- **技术栈**: llama-cpp-python, GGUF格式模型
- **功能**: 客户咨询、产品推荐、价格查询、库存查询、退换货政策
- **运行**: `cd cor-project1 && python task1/task1.py`

### Task 2: 本地对话系统比较
- **目标**: 比较不同LLM架构(编码器-解码器、仅编码器、仅解码器)
- **模型**: Mistral-7B-Instruct, Orca-Mini-3B
- **分析**: 性能对比、应用场景分析、技术特点评估
- **运行**: `cd cor-project1 && python task2/chat_llama_Mistral-7B-Instruct.py`

### Task 4: GUI界面设计
- **目标**: 设计ChatGPT式交互界面
- **技术栈**: tkinter, 多线程处理
- **功能**: 现代化聊天界面、实时对话、模型切换
- **运行**: `cd cor-project1 && python task4/chat_gui.py`

### Task 5: 多模态大语言模型探索
- **目标**: 探索LLaVA多模态大语言模型
- **技术栈**: LLaVA, CLIP, Transformers
- **功能**: 图文对话、图像描述、视觉问答
- **运行**: `cd cor-project1 && task5/llava_project/LLaVA/python predict.py`

## 环境要求

### 系统要求
- Python 3.9
- 8GB+ RAM (推荐16GB+)
- GPU支持 (可选，用于加速推理)

### 硬件建议
- **Task 1-2**: 8GB RAM, 可选GPU
- **Task 4**: 4GB RAM
- **Task 5**: 16GB+ RAM, 推荐GPU (20GB+ VRAM)

## 快速开始

### 1. 环境安装
```bash
# 克隆项目
git clone <repository-url>
cd cor-project1

# 安装依赖
pip install -r requirements.txt

# 安装llama-cpp-python (支持GPU)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

## 技术特点

### 模型支持
- **Mistral-7B-Instruct**: 指令优化模型，适合对话任务
- **Orca-Mini-3B**: 轻量级模型，适合资源受限环境
- **LLaVA-1.5-7B**: 多模态模型，支持图文理解

### 技术栈
- **llama-cpp-python**: 高效的本地模型推理
- **GGUF格式**: 优化的模型存储格式
- **tkinter**: 跨平台GUI框架
- **LLaVA**: 多模态大语言模型框架

### 性能优化
- GPU加速推理
- 量化模型支持
- 多线程处理
- 流式文本生成

## 项目亮点

1. **完整的LLM应用生态**: 从基础对话到多模态AI
2. **性能对比分析**: 详细的模型架构比较
3. **用户友好界面**: 现代化GUI设计
4. **多模态能力**: 图文理解和生成
5. **工程实践**: 完整的项目文档和代码结构

## 报告文档

每个任务都包含详细的技术报告：
- **Task1_Report.md**: 商店接待员系统设计与实现
- **Task2_Report.md**: LLM架构比较分析
- **Task4_Report.md**: GUI设计原理与实践
- **Task5_Report.md**: 多模态模型探索


**注意**: 本项目需要下载大型模型文件，请确保网络连接稳定和足够的存储空间。
