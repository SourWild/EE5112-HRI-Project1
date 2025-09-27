# GitHub 仓库设置指南

## 当前状态
✅ Git仓库已初始化
✅ 文件已提交到本地仓库
✅ .gitignore已配置
✅ 初始提交已完成

## 下一步：创建GitHub仓库

### 1. 在GitHub上创建新仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `EE5112-HCI-LLM-Project` (或您喜欢的名称)
   - **Description**: `EE5112 HCI Course Project - Large Language Models Exploration`
   - **Visibility**: Public (推荐) 或 Private
   - **不要**勾选 "Add a README file" (我们已经有了)
   - **不要**勾选 "Add .gitignore" (我们已经有了)
   - **不要**勾选 "Choose a license" (可选)

### 2. 连接本地仓库到GitHub

创建仓库后，GitHub会显示连接命令。使用以下命令：

```bash
# 添加远程仓库 (替换YOUR_USERNAME和YOUR_REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 推送到GitHub
git push -u origin main
```

### 3. 验证上传

1. 刷新GitHub仓库页面
2. 确认所有文件都已上传
3. 检查README.md是否正确显示

## 仓库结构说明

```
EE5112-HCI-LLM-Project/
├── README.md              # 项目主文档
├── requirements.txt       # 依赖列表
├── .gitignore            # Git忽略文件
├── task1/                # 商店接待员系统
│   ├── task1.py
│   ├── download_model.py
│   ├── Task1_Report.md
│   └── picture.pptx
├── task2/                # LLM比较分析
│   ├── chat_llama_Mistral-7B-Instruct.py
│   ├── chat_llama_Orca-Mini-3B.py
│   └── Task2_Report.md
├── task4/                # GUI界面设计
│   ├── chat_gui.py
│   ├── chat_backend.py
│   └── Task4_Report.md
└── task5/                # 多模态模型
    ├── Task5_Report.md
    └── llava_project/    # LLaVA项目 (需要单独处理)
```

## 注意事项

### LLaVA项目处理
由于LLaVA是一个独立的Git仓库，您有两个选择：

1. **作为子模块添加** (推荐):
```bash
cd task5/llava_project/
git submodule add https://github.com/haotian-liu/LLaVA.git LLaVA
```

2. **或者删除LLaVA目录**，在README中说明用户需要单独下载

### 模型文件
- 大型模型文件(.gguf, .bin)已被.gitignore忽略
- 用户需要按照README中的说明下载模型

## 后续维护

### 更新仓库
```bash
# 添加更改
git add .

# 提交更改
git commit -m "描述您的更改"

# 推送到GitHub
git push
```

### 添加标签
```bash
# 为重要版本添加标签
git tag -a v1.0 -m "Initial release with all 4 tasks"
git push origin v1.0
```

## 仓库设置建议

1. **添加Topics**: 在GitHub仓库设置中添加相关标签
   - `llm`
   - `hci`
   - `multimodal`
   - `python`
   - `education`

2. **启用Issues**: 允许用户报告问题

3. **添加License**: 考虑添加适当的开源许可证

4. **设置分支保护**: 保护main分支，要求PR审查

完成这些步骤后，您的项目就成功上传到GitHub了！
