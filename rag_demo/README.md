# 空头报告反驳助手 (Short Report Rebuttal Assistant)

一个基于RAG（检索增强生成）的MVP系统，用于分析空头报告并生成反驳分析。

## 项目结构

```
rag_demo/
├── backend/              # FastAPI 后端
│   ├── app/             # 应用模块
│   ├── main.py          # FastAPI 主应用
│   ├── requirements.txt # Python 依赖
│   └── .env.example     # 环境变量示例
├── frontend/            # React 前端
│   ├── src/             # React 源代码
│   ├── package.json     # Node.js 依赖
│   └── vite.config.js   # Vite 配置
├── company/             # 内部文档目录
│   └── EDU/
├── storage/             # 数据存储
│   ├── chroma/         # ChromaDB 向量数据库
│   └── reports/        # 生成的报告
└── run.sh              # 启动脚本
```

## 快速开始

### 1. 安装Ollama并下载模型

```bash
# 安装Ollama (访问 https://ollama.ai)
# 下载模型
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件（如果需要）
```

### 5. 索引内部文档

```bash
cd backend
python -m app.index_internal
```

### 6. 启动服务

```bash
# 在项目根目录
./run.sh
```

或者分别启动：

**后端:**
```bash
cd backend
uvicorn main:app --reload
```

**前端:**
```bash
cd frontend
npm run dev
```

## 访问地址

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **API测试**: 运行 `./test_api.sh` 或 `python test_api.py`

## 技术栈

### 后端
- FastAPI
- ChromaDB (向量数据库)
- Ollama (LLM和嵌入)

### 前端
- React 18
- Vite
- Axios

## 功能特性

- 📄 PDF处理: 自动提取空头报告前3页内容
- 🔍 论点提取: 使用LLM识别独立、可测试的论点
- 📚 证据检索: 从本地向量数据库检索相关内部证据
- ⚖️ 智能判断: 评估每个论点的覆盖情况
- 📊 报告生成: 生成分析师风格的分析报告

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

## 故障排除

### Ollama连接失败
```bash
ollama serve
```

### 端口被占用
- 后端默认端口: 8000
- 前端默认端口: 3000

可以在配置文件中修改

## API 文档

详细的 API 文档和使用说明请查看：
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - 完整的 API 文档和使用指南

## 测试 API

### 使用测试脚本

**Shell 脚本**:
```bash
./test_api.sh
```

**Python 脚本**:
```bash
python test_api.py
```

测试脚本会验证：
- Ollama 服务连接
- 后端 REST API 端点
- 向量数据库状态
- 完整的上传→分析流程

## 许可证

MIT License
