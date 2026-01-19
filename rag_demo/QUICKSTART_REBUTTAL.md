# 快速开始指南

## 1. 环境准备

### 安装Ollama

```bash
# macOS
brew install ollama

# 或访问 https://ollama.ai 下载安装包
```

### 启动Ollama并下载模型

```bash
# 启动Ollama服务（如果未自动启动）
ollama serve

# 在另一个终端下载模型
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 安装Python依赖

```bash
cd rag_demo
pip install -r requirements_rebuttal.txt
```

## 2. 配置

```bash
# 复制环境配置文件
cp sample.env .env

# 编辑 .env（如果需要修改默认配置）
# 默认配置通常可以直接使用
```

## 3. 准备内部文档

将内部文档（PDF/TXT/MD/DOCX）放入 `./company/EDU/` 目录。

示例：
```bash
company/EDU/
├── company_data.pdf
├── financial_report_2023.pdf
├── audit_letter.txt
└── contracts.docx
```

## 4. 索引内部文档

```bash
python -m app.index_internal
```

这将：
- 加载所有内部文档
- 分块并生成嵌入
- 存储到ChromaDB

## 5. 启动服务

### 方法A: 使用启动脚本（推荐）

```bash
./run_rebuttal.sh
```

### 方法B: 手动启动

#### 终端1: FastAPI后端
```bash
uvicorn main:app --reload
```

#### 终端2: Streamlit UI
```bash
streamlit run streamlit_app.py
```

## 6. 使用系统

### 通过Streamlit UI

1. 打开浏览器访问 `http://localhost:8501`
2. 在"上传报告"标签页上传PDF
3. 在"分析"标签页点击"开始分析"
4. 在"下载报告"标签页下载结果

### 通过API

#### 上传报告
```bash
curl -X POST "http://localhost:8000/upload_report" \
  -F "file=@short_report.pdf"
```

#### 分析报告
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "your-report-id",
    "top_k": 6,
    "max_claims": 30
  }'
```

#### 查看API文档
访问 `http://localhost:8000/docs`

## 7. 输出文件

所有生成的文件保存在 `./storage/reports/` 目录：

- `{report_id}.pdf` - 原始上传的PDF
- `{report_id}.claims.json` - 提取的论点（缓存）
- `{report_id}.report.json` - JSON格式的分析报告
- `{report_id}.report.md` - Markdown格式的分析报告

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

## 性能提示

- **首次运行较慢**: 需要下载模型和索引文档
- **分析时间**: 取决于论点和文档数量（通常5-15分钟）
- **内存使用**: 建议至少8GB RAM，推荐16GB
- **并行处理**: 可以同时处理多个报告（使用不同的report_id）

## 下一步

- 查看 `README_REBUTTAL.md` 了解详细文档
- 查看 `app/judge.py` 了解评判标准
- 自定义 `.env` 配置以优化性能
