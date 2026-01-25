# 快速开始指南 - 前后端分离版本

## 项目结构

```
rag_demo/
├── backend/          # FastAPI 后端
│   ├── app/         # 应用模块
│   ├── main.py      # FastAPI 主应用
│   └── requirements.txt
├── frontend/         # React 前端
│   ├── src/         # React 源代码
│   └── package.json
├── company/          # 内部文档
├── storage/          # 数据存储
└── run.sh           # 启动脚本
```

## 快速开始（3步）

### 1. 安装依赖

**后端:**
```bash
cd backend
pip install -r requirements.txt
```

**前端:**
```bash
cd frontend
npm install
```

### 2. 配置环境

```bash
cd backend
cp .env.example .env
# 编辑 .env（如果需要）
```

### 3. 启动服务

**方法A: 使用启动脚本（推荐）**
```bash
./run.sh
```

**方法B: 手动启动**

终端1 - 后端:
```bash
cd backend
uvicorn main:app --reload
```

终端2 - 前端:
```bash
cd frontend
npm run dev
```

## 访问地址

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 首次运行前的准备

### 1. 安装Ollama并下载模型

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 2. 索引内部文档

```bash
cd backend
python -m app.index_internal
```

## 开发

### 后端开发

```bash
cd backend
uvicorn main:app --reload
```

### 前端开发

```bash
cd frontend
npm run dev
```

## 构建生产版本

### 前端

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist/` 目录

## API端点

所有API端点都以 `/api` 为前缀：

- `POST /api/upload_report` - 上传报告
- `POST /api/analyze` - 分析报告
- `GET /api/download_report/{report_id}` - 下载报告

## 故障排除

### 端口被占用

- 后端: 修改 `backend/main.py` 中的端口
- 前端: 修改 `frontend/vite.config.js` 中的端口

### CORS错误

确保后端 `main.py` 中的 CORS 配置包含前端地址

### 路径错误

确保 `backend/app/config.py` 中的路径配置正确
