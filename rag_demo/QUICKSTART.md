# 快速开始指南

## 🚀 三步启动应用

### 1️⃣ 设置环境（首次运行）

```bash
cd /Users/andyli/projects/galaxy_test/wk2_RAG/rag_demo
bash setup.sh
```

### 2️⃣ 配置 API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3️⃣ 运行应用

```bash
bash run.sh
```

或者：

```bash
source venv/bin/activate
streamlit run app.py
```

---

## 📋 详细步骤

### 步骤 1: 进入项目目录

```bash
cd /Users/andyli/projects/galaxy_test/wk2_RAG/rag_demo
```

### 步骤 2: 创建并激活虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
```

### 步骤 3: 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤 4: 设置环境变量

```bash
export OPENAI_API_KEY="sk-your-api-key"
```

### 步骤 5: 运行应用

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`

---

## ✅ 验证安装

运行以下命令检查：

```bash
python -c "import streamlit, faiss, openai; print('✓ 所有依赖已安装')"
```

---

## 📖 更多信息

- 详细设置指南: `SETUP_GUIDE.md`
- 使用说明: `README_STREAMLIT.md`
