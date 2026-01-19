# 空头报告反驳助手 (Short Report Rebuttal Assistant)

一个基于RAG（检索增强生成）的MVP系统，用于分析空头报告并生成反驳分析。

## 功能特性

- 📄 **PDF处理**: 自动提取空头报告前3页内容
- 🔍 **论点提取**: 使用LLM识别独立、可测试的论点（8-30个）
- 📚 **证据检索**: 从本地向量数据库检索相关内部证据
- ⚖️ **智能判断**: 评估每个论点的覆盖情况（完全解决/部分解决/未解决）
- 📊 **报告生成**: 生成分析师风格的分析报告（Markdown + JSON）

## 技术栈

- **后端**: FastAPI
- **前端**: Streamlit
- **LLM**: Ollama (本地运行)
- **嵌入模型**: Ollama (nomic-embed-text)
- **向量数据库**: ChromaDB (本地持久化)
- **PDF处理**: pypdf / pdfplumber

## 系统要求

- Python 3.11+
- Ollama (已安装并运行)
- 至少8GB RAM (推荐16GB)

## 安装步骤

### 1. 安装Ollama

访问 [https://ollama.ai](https://ollama.ai) 下载并安装Ollama。

### 2. 下载Ollama模型

```bash
# 下载LLM模型
ollama pull llama3.1

# 下载嵌入模型
ollama pull nomic-embed-text
```

### 3. 安装Python依赖

```bash
cd rag_demo
pip install -r requirements_rebuttal.txt
```

### 4. 配置环境变量

复制示例环境文件并编辑：

```bash
cp sample.env .env
```

编辑 `.env` 文件，确保Ollama配置正确：

```env
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1
EMBED_MODEL=nomic-embed-text
```

### 5. 准备内部文档

将内部文档（PDF/TXT/MD/DOCX）放置在 `./company/EDU/` 目录下。

### 6. 索引内部文档

运行索引脚本，将内部文档加载到向量数据库：

```bash
python -m app.index_internal
```

这会将所有内部文档分块、嵌入并存储到ChromaDB中。

## 使用方法

### 方法1: 使用FastAPI + Streamlit UI

#### 启动FastAPI后端

```bash
uvicorn main:app --reload
```

API将在 `http://localhost:8000` 运行。

#### 启动Streamlit UI

在另一个终端：

```bash
streamlit run streamlit_app.py
```

UI将在 `http://localhost:8501` 运行。

### 方法2: 仅使用FastAPI (命令行)

#### 上传报告

```bash
curl -X POST "http://localhost:8000/upload_report" \
  -F "file=@short_report.pdf"
```

响应示例：
```json
{
  "report_id": "uuid-here",
  "claims": [...],
  "message": "Successfully uploaded and extracted 15 claims"
}
```

#### 分析报告

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "uuid-here",
    "top_k": 6,
    "max_claims": 30
  }'
```

#### 下载报告

```bash
# Markdown格式
curl -O "http://localhost:8000/download_report/{report_id}?format=md"

# JSON格式
curl -O "http://localhost:8000/download_report/{report_id}?format=json"
```

## API端点

### `POST /upload_report`

上传空头报告PDF并提取论点。

**请求**: 
- `file`: PDF文件 (multipart/form-data)

**响应**:
- `report_id`: 报告唯一标识符
- `claims`: 提取的论点列表
- `message`: 状态消息

### `POST /analyze`

分析论点并生成报告。

**请求**:
```json
{
  "report_id": "uuid",
  "top_k": 6,
  "max_claims": 30
}
```

**响应**:
- `report`: 完整的分析报告（包含Markdown和JSON）

### `GET /download_report/{report_id}`

下载生成的报告。

**参数**:
- `format`: "md" 或 "json"

## 项目结构

```
rag_demo/
├── app/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── models.py           # Pydantic模型
│   ├── utils.py            # 工具函数
│   ├── pdf_extract.py      # PDF提取
│   ├── claim_extract.py    # 论点提取
│   ├── index_internal.py   # 内部文档索引
│   ├── retrieval.py        # 证据检索
│   ├── judge.py            # 论点判断
│   └── report.py           # 报告生成
├── main.py                 # FastAPI应用
├── streamlit_app.py        # Streamlit UI
├── requirements_rebuttal.txt
├── sample.env
├── README_REBUTTAL.md
├── company/
│   └── EDU/                # 内部文档目录
│       └── company_data.pdf
└── storage/
    ├── chroma/             # ChromaDB存储
    └── reports/            # 生成的报告
```

## 工作流程

1. **索引阶段** (一次性):
   - 加载内部文档 (`./company/EDU/`)
   - 分块、嵌入
   - 存储到ChromaDB

2. **上传阶段**:
   - 用户上传空头报告PDF
   - 提取前3页文本
   - 使用LLM提取论点（8-30个）
   - 保存到 `./storage/reports/{report_id}.pdf` 和 `.claims.json`

3. **分析阶段**:
   - 对每个论点：
     - 检索top_k个相关文档
     - 使用LLM判断覆盖情况
     - 生成分析（推理、引用、置信度、缺口、建议）
   - 生成完整报告（Markdown + JSON）

## 论点分类

- **accounting**: 会计违规、财务错报
- **business_model**: 商业模式担忧、可持续性问题
- **fraud**: 欺诈指控、欺骗行为
- **related_party**: 关联方交易、利益冲突
- **guidance**: 指引操纵、前瞻性声明
- **metrics**: 关键指标操纵、KPI问题
- **other**: 其他类型

## 覆盖情况分类

- **fully_addressed**: 内部证据直接、明确地反驳了论点
- **partially_addressed**: 部分相关，但不够完整
- **not_addressed**: 证据不相关或非常薄弱

## 评判标准

系统使用严格的评判标准（见 `app/judge.py` 中的 `JUDGMENT_CRITERIA`）：

- 必须引用证据片段（文档名称 + 分块ID）
- 如果证据薄弱或不相关，必须分类为"未解决"
- 如果未完全解决，必须列出缺失的证据类型
- 提供IR/法律/财务部门的后续步骤建议

## 故障排除

### Ollama连接失败

确保Ollama正在运行：

```bash
ollama serve
```

检查模型是否已下载：

```bash
ollama list
```

### ChromaDB集合不存在

运行索引脚本：

```bash
python -m app.index_internal
```

### PDF提取失败

尝试安装pdfplumber作为备选：

```bash
pip install pdfplumber
```

### 内存不足

- 减少 `MAX_CLAIMS`
- 减少 `top_k`
- 减少 `CHUNK_SIZE`

## 性能优化

- 使用缓存：提取的论点存储在 `./storage/reports/{report_id}.claims.json`
- 批量处理：嵌入和索引使用批量处理
- 配置参数：根据硬件调整 `top_k`、`max_claims` 等

## 限制

- 仅处理PDF前3页
- 需要本地运行Ollama（无外部网络调用）
- 内部文档必须预先索引
- 处理时间取决于论点和文档数量

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
