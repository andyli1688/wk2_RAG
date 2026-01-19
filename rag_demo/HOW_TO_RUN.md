# 如何运行空头报告反驳助手

## 快速开始（3步）

### 步骤1: 确保Ollama运行并下载模型

```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 如果失败，启动Ollama（如果未自动启动）
ollama serve

# 在另一个终端下载必需的模型
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 步骤2: 安装Python依赖

```bash
cd rag_demo
pip install -r requirements_rebuttal.txt
```

### 步骤3: 运行系统

#### 方法A: 使用启动脚本（推荐）

```bash
./run_rebuttal.sh
```

这个脚本会：
- ✅ 检查Ollama连接
- ✅ 检查模型是否已下载
- ✅ 自动索引内部文档（如果需要）
- ✅ 启动FastAPI服务器

#### 方法B: 手动启动

**终端1 - 启动FastAPI后端：**
```bash
cd rag_demo
uvicorn main:app --reload
```

**终端2 - 启动Streamlit UI：**
```bash
cd rag_demo
streamlit run streamlit_app.py
```

## 详细步骤

### 1. 环境准备

#### 安装Ollama
- macOS: `brew install ollama` 或访问 https://ollama.ai 下载
- Linux: 访问 https://ollama.ai 下载
- Windows: 访问 https://ollama.ai 下载

#### 下载模型
```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 2. Python环境设置

```bash
# 进入项目目录
cd rag_demo

# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements_rebuttal.txt
```

### 3. 配置环境变量

```bash
# 复制示例配置文件
cp sample.env .env

# 编辑 .env（如果需要修改默认配置）
# 默认配置通常可以直接使用
```

### 4. 准备内部文档

将内部文档放入 `./company/EDU/` 目录：

```bash
company/EDU/
├── company_data.pdf
├── financial_report.pdf
├── audit_letter.txt
└── contracts.docx
```

### 5. 索引内部文档（一次性）

```bash
python -m app.index_internal
```

这会：
- 加载所有内部文档
- 分块并生成嵌入向量
- 存储到ChromaDB

**注意**: 如果 `storage/chroma/` 目录已存在且有数据，可以跳过此步骤。

### 6. 启动服务

#### 选项A: 使用启动脚本

```bash
chmod +x run_rebuttal.sh
./run_rebuttal.sh
```

#### 选项B: 手动启动

**启动FastAPI（终端1）：**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动Streamlit UI（终端2）：**
```bash
streamlit run streamlit_app.py
```

### 7. 访问应用

- **Streamlit UI**: http://localhost:8501
- **FastAPI API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 使用流程

### 通过Streamlit UI

1. 打开浏览器访问 http://localhost:8501
2. **上传报告**标签页：
   - 点击"选择PDF文件"
   - 选择空头报告PDF
   - 点击"上传并提取论点"
   - 等待提取完成（会显示提取的论点列表）
3. **分析**标签页：
   - 调整参数（检索文档数量、最大分析论点数）
   - 点击"开始分析"
   - 等待分析完成（可能需要几分钟）
   - 查看执行摘要和详细分析
4. **下载报告**标签页：
   - 点击"下载Markdown报告"或"下载JSON报告"
   - 保存文件到本地

### 通过API（命令行）

#### 1. 上传报告
```bash
curl -X POST "http://localhost:8000/upload_report" \
  -F "file=@your_short_report.pdf"
```

响应示例：
```json
{
  "report_id": "abc123-def456-...",
  "claims": [...],
  "message": "Successfully uploaded and extracted 15 claims"
}
```

#### 2. 分析报告
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "abc123-def456-...",
    "top_k": 6,
    "max_claims": 30
  }'
```

#### 3. 下载报告
```bash
# Markdown格式
curl -O "http://localhost:8000/download_report/abc123-def456-...?format=md"

# JSON格式
curl -O "http://localhost:8000/download_report/abc123-def456-...?format=json"
```

## 故障排除

### Ollama连接失败

```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 如果失败，启动Ollama
ollama serve
```

### 模型未找到

```bash
# 列出已安装的模型
ollama list

# 下载缺失的模型
ollama pull llama3.1
ollama pull nomic-embed-text
```

### ChromaDB集合不存在

```bash
# 重新运行索引
python -m app.index_internal
```

### PDF提取失败

```bash
# 安装备选PDF库
pip install pdfplumber
```

### 端口被占用

```bash
# 修改端口（FastAPI）
uvicorn main:app --reload --port 8001

# 修改端口（Streamlit）
streamlit run streamlit_app.py --server.port 8502
```

### 依赖包缺失

```bash
# 重新安装所有依赖
pip install -r requirements_rebuttal.txt
```

## 输出文件位置

所有生成的文件保存在 `./storage/reports/` 目录：

- `{report_id}.pdf` - 原始上传的PDF
- `{report_id}.claims.json` - 提取的论点（缓存）
- `{report_id}.report.json` - JSON格式的分析报告
- `{report_id}.report.md` - Markdown格式的分析报告

## 性能提示

- **首次运行**: 需要下载模型和索引文档，可能需要较长时间
- **分析时间**: 取决于论点和文档数量（通常5-15分钟）
- **内存使用**: 建议至少8GB RAM，推荐16GB
- **并行处理**: 可以同时处理多个报告（使用不同的report_id）

## 下一步

- 查看 `README_REBUTTAL.md` 了解完整文档
- 查看 `app/judge.py` 了解评判标准
- 自定义 `.env` 配置以优化性能
