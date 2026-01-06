# RAG Demo 完整设置指南

本指南将帮助您从头开始设置和运行 RAG 问答助手应用。

## 前置要求

- Python 3.8 或更高版本
- pip（Python 包管理器）
- 网络连接（用于下载依赖和访问 API）

## 快速开始

### 方法一：使用自动化脚本（推荐）

#### 1. 设置环境并安装依赖

```bash
cd /Users/andyli/projects/galaxy_test/wk2_RAG/rag_demo
bash setup.sh
```

这个脚本会：
- 检查 Python 版本
- 创建虚拟环境
- 安装所有必需的依赖包

#### 2. 配置环境变量

设置 OpenAI API Key：

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

或者创建 `.env` 文件（需要安装 python-dotenv）：

```bash
echo "OPENAI_API_KEY=your-openai-api-key-here" > .env
```

#### 3. 运行应用

```bash
bash run.sh
```

或者手动运行：

```bash
source venv/bin/activate
streamlit run app.py
```

---

### 方法二：手动设置

#### 步骤 1: 创建虚拟环境

```bash
cd /Users/andyli/projects/galaxy_test/wk2_RAG/rag_demo
python3 -m venv venv
```

#### 步骤 2: 激活虚拟环境

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

激活成功后，命令行提示符前会显示 `(venv)`。

#### 步骤 3: 升级 pip

```bash
pip install --upgrade pip
```

#### 步骤 4: 安装依赖

```bash
pip install -r requirements.txt
```

这将安装以下主要包：
- `streamlit` - Web 应用框架
- `faiss-cpu` - 向量相似度搜索
- `langchain-community` - 文档处理
- `openai` - OpenAI API 客户端
- `pymupdf` - PDF 处理
- 以及其他依赖

#### 步骤 5: 配置环境变量

**设置 OpenAI API Key:**

```bash
# macOS/Linux
export OPENAI_API_KEY="sk-your-api-key-here"

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Windows (CMD)
set OPENAI_API_KEY=sk-your-api-key-here
```

**验证设置:**
```bash
echo $OPENAI_API_KEY  # macOS/Linux
echo %OPENAI_API_KEY%  # Windows CMD
```

#### 步骤 6: 运行应用

```bash
streamlit run app.py
```

应用会自动在浏览器中打开，默认地址：`http://localhost:8501`

---

## 详细配置说明

### 1. 嵌入服务配置

默认使用 `http://test.2brain.cn:9800/v1/emb` 作为嵌入服务。

如需修改，编辑 `embedding.py`：

```python
EMBEDDING_URL = "http://your-embedding-service-url/v1/emb"
```

### 2. OpenAI 模型配置

默认使用 `gpt-4o` 模型。如需修改，编辑 `generation.py` 中的 `generate_answer` 函数：

```python
def generate_answer(..., model: str = "gpt-3.5-turbo", ...):
```

### 3. FAISS 索引配置

索引文件保存在 `faiss_out/` 目录：
- `rag.index.faiss` - FAISS 索引文件
- `rag.meta.json` - 文档元数据

### 4. 上传文件目录

上传的 PDF 文件保存在 `uploads/` 目录。

---

## 验证安装

运行以下命令验证所有依赖是否正确安装：

```bash
python -c "import streamlit; import faiss; import openai; print('✓ 所有依赖已正确安装')"
```

---

## 常见问题

### 问题 1: 虚拟环境激活失败

**解决方案:**
- 确保使用正确的激活命令（macOS/Linux vs Windows）
- 检查虚拟环境是否已创建：`ls venv/` 或 `dir venv`

### 问题 2: pip 安装失败

**解决方案:**
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像（如果网络较慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3: OpenAI API 错误

**解决方案:**
- 检查 API Key 是否正确设置：`echo $OPENAI_API_KEY`
- 确认账户有足够的额度
- 检查网络连接

### 问题 4: 嵌入服务连接失败

**解决方案:**
- 检查 `embedding.py` 中的 URL 是否正确
- 确认服务是否可访问：`curl http://test.2brain.cn:9800/v1/emb`
- 检查防火墙设置

### 问题 5: FAISS 安装问题

**解决方案:**
```bash
# 如果 faiss-cpu 安装失败，尝试：
pip install faiss-cpu --no-cache-dir

# 或者使用 conda（如果已安装）
conda install -c conda-forge faiss-cpu
```

### 问题 6: Streamlit 无法启动

**解决方案:**
```bash
# 检查端口是否被占用
lsof -i :8501  # macOS/Linux
netstat -ano | findstr :8501  # Windows

# 使用其他端口
streamlit run app.py --server.port 8502
```

---

## 项目结构

```
rag_demo/
├── app.py                    # Streamlit 主应用
├── document_process.py       # 文档处理模块
├── embedding.py              # 向量嵌入模块
├── faiss_demo.py            # FAISS 索引管理
├── generation.py            # 答案生成模块
├── requirements.txt         # 依赖列表
├── setup.sh                # 环境设置脚本
├── run.sh                   # 运行脚本
├── SETUP_GUIDE.md          # 本指南
├── README_STREAMLIT.md      # 使用说明
├── uploads/                # 上传文件目录（自动创建）
└── faiss_out/              # 索引文件目录（自动创建）
```

---

## 下一步

1. **上传文档**: 在应用界面左侧上传 PDF 文档
2. **处理文档**: 点击"处理文档"按钮，等待处理完成
3. **开始问答**: 在主页输入问题并提交

详细使用说明请参考 `README_STREAMLIT.md`。

---

## 获取帮助

如果遇到问题：
1. 检查本文档的"常见问题"部分
2. 查看错误日志信息
3. 确认所有依赖都已正确安装
4. 验证环境变量配置

---

## 卸载

如需完全卸载：

```bash
# 删除虚拟环境
rm -rf venv

# 删除生成的文件（可选）
rm -rf uploads faiss_out

# 删除 Python 缓存
find . -type d -name __pycache__ -exec rm -r {} +
```
