# API 文档和使用说明

## 目录
1. [大模型 API](#大模型-api)
2. [后端 REST API](#后端-rest-api)
3. [API 测试方法](#api-测试方法)
4. [使用示例](#使用示例)

---

## 大模型 API

### Ollama API

本项目使用 **Ollama** 作为本地大模型服务，提供以下功能：

#### 1. LLM 文本生成 API

**端点**: `POST http://localhost:11434/api/chat`

**用途**: 
- 提取空头报告中的论点（Claims）
- 分析论点与证据的覆盖情况（Judgment）
- 生成分析推理和推荐行动

**使用的模型**: `llama3.1:8b`

**请求示例**:
```json
{
  "model": "llama3.1:8b",
  "messages": [
    {
      "role": "system",
      "content": "You are a financial analyst expert..."
    },
    {
      "role": "user",
      "content": "Extract claims from the following report..."
    }
  ],
  "options": {
    "temperature": 0.3,
    "num_predict": 2000
  },
  "stream": false
}
```

**在后端代码中的使用位置**:
- `backend/app/claim_extract.py` - 论点提取
- `backend/app/judge.py` - 论点判断和分析

#### 2. 文本嵌入 API

**端点**: `POST http://localhost:11434/api/embeddings`

**用途**: 
- 将文档和查询文本转换为向量嵌入
- 用于向量数据库检索

**使用的模型**: `nomic-embed-text`

**请求示例**:
```json
{
  "model": "nomic-embed-text",
  "prompt": "文本内容..."
}
```

**在后端代码中的使用位置**:
- `backend/app/index_internal.py` - 文档索引时的嵌入生成
- `backend/app/retrieval.py` - 查询时的嵌入生成

---

## 后端 REST API

### FastAPI 服务

**基础URL**: `http://localhost:8000`

**API 文档**: `http://localhost:8000/docs` (Swagger UI)

**ReDoc 文档**: `http://localhost:8000/redoc`

### API 端点列表

#### 1. 健康检查

**端点**: `GET /health`

**描述**: 检查服务状态和向量数据库状态

**响应示例**:
```json
{
  "status": "healthy",
  "chroma_db_exists": true,
  "collection_exists": true,
  "collection_count": 150,
  "reports_dir": "/path/to/storage/reports"
}
```

**测试命令**:
```bash
curl http://localhost:8000/health
```

#### 2. 根端点

**端点**: `GET /`

**描述**: 返回 API 基本信息

**响应示例**:
```json
{
  "message": "Short Report Rebuttal Assistant API",
  "version": "1.0.0",
  "endpoints": {
    "upload": "/api/upload_report",
    "analyze": "/api/analyze",
    "download": "/api/download_report/{report_id}"
  }
}
```

#### 3. 上传报告

**端点**: `POST /api/upload_report`

**描述**: 上传空头报告 PDF 并提取论点

**请求**:
- **Content-Type**: `multipart/form-data`
- **参数**: `file` (PDF 文件)

**响应示例**:
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "claims": [
    {
      "claim_id": "C001",
      "claim_text": "公司存在财务造假...",
      "page_numbers": [1, 2],
      "claim_type": "accounting"
    }
  ],
  "message": "Successfully uploaded and extracted 15 claims"
}
```

**测试命令**:
```bash
curl -X POST http://localhost:8000/api/upload_report \
  -F "file=@/path/to/report.pdf"
```

#### 4. 分析论点

**端点**: `POST /api/analyze`

**描述**: 分析已上传报告的论点，检索证据并生成分析报告

**请求体**:
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "top_k": 6,
  "max_claims": 30
}
```

**参数说明**:
- `report_id`: 报告ID（从上传接口获取）
- `top_k`: 每个论点检索的文档数量（默认: 6）
- `max_claims`: 最大分析论点数（默认: 30）

**响应示例**:
```json
{
  "report": {
    "report_id": "550e8400-e29b-41d4-a716-446655440000",
    "generated_at": "2024-01-24T22:00:00",
    "summary": {
      "total_claims": 15,
      "fully_addressed": 8,
      "partially_addressed": 5,
      "not_addressed": 2,
      "average_confidence": 75.5,
      "key_gaps": ["审计报告", "合同文件"],
      "priority_actions": ["收集更多证据", "咨询财务部门"]
    },
    "claim_analyses": [
      {
        "claim_id": "C001",
        "coverage": "fully_addressed",
        "reasoning": "• 根据证据1，公司财报显示...",
        "citations": [
          {
            "doc_id": "company_data",
            "doc_title": "company_data.pdf",
            "chunk_id": "company_data_chunk_0",
            "quote": "相关证据文本...",
            "similarity_score": 0.85
          }
        ],
        "confidence": 90,
        "gaps": null,
        "recommended_actions": null
      }
    ],
    "markdown": "# 分析报告\n\n...",
    "json": {...}
  },
  "message": "Successfully analyzed 15 claims"
}
```

**测试命令**:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "550e8400-e29b-41d4-a716-446655440000",
    "top_k": 6,
    "max_claims": 30
  }'
```

#### 5. 检查并索引向量数据库

**端点**: `POST /api/check_and_index`

**描述**: 检查向量数据库状态，如果不存在或为空则自动索引 `company/EDU/company_data.pdf`

**响应示例**:
```json
{
  "indexed": true,
  "message": "Successfully indexed 150 chunks",
  "count": 150
}
```

**测试命令**:
```bash
curl -X POST http://localhost:8000/api/check_and_index
```

#### 6. 下载报告

**端点**: `GET /api/download_report/{report_id}?format={format}`

**描述**: 下载生成的分析报告

**参数**:
- `report_id`: 报告ID
- `format`: 报告格式 (`md` 或 `json`)

**测试命令**:
```bash
# 下载 Markdown 格式
curl http://localhost:8000/api/download_report/550e8400-e29b-41d4-a716-446655440000?format=md -o report.md

# 下载 JSON 格式
curl http://localhost:8000/api/download_report/550e8400-e29b-41d4-a716-446655440000?format=json -o report.json
```

---

## API 测试方法

### 1. 使用 Swagger UI 测试

1. 启动后端服务：
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. 打开浏览器访问：`http://localhost:8000/docs`

3. 在 Swagger UI 中：
   - 查看所有可用端点
   - 点击端点查看详细信息
   - 点击 "Try it out" 测试端点
   - 查看请求/响应示例

### 2. 使用 curl 测试

#### 测试健康检查
```bash
curl http://localhost:8000/health | jq
```

#### 测试上传报告
```bash
curl -X POST http://localhost:8000/api/upload_report \
  -F "file=@./test_report.pdf" \
  | jq
```

#### 测试分析
```bash
# 先获取 report_id（从上一步的响应中）
REPORT_ID="your-report-id-here"

curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"report_id\": \"$REPORT_ID\",
    \"top_k\": 6,
    \"max_claims\": 30
  }" | jq
```

### 3. 使用 Python 测试

创建测试脚本 `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. 健康检查
response = requests.get(f"{BASE_URL}/health")
print("Health Check:", response.json())

# 2. 上传报告
with open("test_report.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/api/upload_report", files=files)
    result = response.json()
    print("Upload Result:", json.dumps(result, indent=2, ensure_ascii=False))
    report_id = result["report_id"]

# 3. 分析报告
payload = {
    "report_id": report_id,
    "top_k": 6,
    "max_claims": 30
}
response = requests.post(f"{BASE_URL}/api/analyze", json=payload)
result = response.json()
print("Analysis Result:", json.dumps(result, indent=2, ensure_ascii=False))
```

运行测试：
```bash
python test_api.py
```

---

## 使用示例

### 完整工作流程

#### 1. 启动服务

```bash
# 启动 Ollama（如果未运行）
ollama serve

# 启动后端服务
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 检查向量数据库

```bash
curl -X POST http://localhost:8000/api/check_and_index
```

#### 3. 上传报告

```bash
curl -X POST http://localhost:8000/api/upload_report \
  -F "file=@./short_report.pdf" \
  -o upload_response.json

# 查看响应
cat upload_response.json | jq
```

#### 4. 分析报告

```bash
# 从 upload_response.json 中获取 report_id
REPORT_ID=$(cat upload_response.json | jq -r '.report_id')

curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"report_id\": \"$REPORT_ID\",
    \"top_k\": 6,
    \"max_claims\": 30
  }" \
  -o analysis_response.json

# 查看分析结果
cat analysis_response.json | jq '.report.summary'
```

#### 5. 下载报告

```bash
# 下载 Markdown 报告
curl http://localhost:8000/api/download_report/$REPORT_ID?format=md \
  -o report.md

# 下载 JSON 报告
curl http://localhost:8000/api/download_report/$REPORT_ID?format=json \
  -o report.json
```

---

## API 调用流程图

```
用户/前端
    │
    ├─→ POST /api/upload_report
    │   └─→ 提取PDF文本（前3页）
    │       └─→ 调用 Ollama LLM API 提取论点
    │           └─→ 返回论点列表
    │
    ├─→ POST /api/analyze
    │   ├─→ 对每个论点：
    │   │   ├─→ 调用 Ollama Embedding API 生成查询向量
    │   │   ├─→ 从 ChromaDB 检索相关文档
    │   │   └─→ 调用 Ollama LLM API 分析覆盖情况
    │   └─→ 生成完整分析报告
    │
    └─→ GET /api/download_report/{report_id}
        └─→ 返回 Markdown 或 JSON 格式报告
```

## 验证 API 正常工作的方法

### 1. 检查 Ollama 服务

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 应该返回已安装的模型列表
```

### 2. 检查后端服务

```bash
# 检查健康状态
curl http://localhost:8000/health

# 应该返回：
# {
#   "status": "healthy",
#   "chroma_db_exists": true,
#   "collection_exists": true,
#   "collection_count": 150
# }
```

### 3. 测试完整流程

使用提供的测试脚本或 Swagger UI 测试完整的上传→分析→下载流程。

---

## 截图说明

### 1. Swagger UI 截图位置

访问 `http://localhost:8000/docs` 可以截图：
- API 端点列表
- 端点详细信息
- 测试界面

### 2. 测试结果截图

可以截图：
- curl 命令执行结果
- Swagger UI 中的测试结果
- 前端界面显示的分析结果

### 3. 日志截图

后端日志位置：`/tmp/backend.log`

可以截图显示：
- API 调用日志
- Ollama API 调用日志
- 向量数据库操作日志

---

## 故障排除

### Ollama API 连接失败

**错误**: `ConnectionError: Failed to connect to Ollama`

**解决方法**:
1. 确保 Ollama 服务正在运行：`ollama serve`
2. 检查端口是否正确：默认 `http://localhost:11434`
3. 检查模型是否已安装：`ollama list`

### 向量数据库未找到

**错误**: `Collection [internal_documents] does not exist`

**解决方法**:
1. 调用 `/api/check_and_index` 端点自动索引
2. 或手动运行：`cd backend && python -m app.index_internal`

### PDF 提取失败

**错误**: `No documents found` 或 `Failed to extract text from PDF`

**解决方法**:
1. 确保安装了 PDF 库：`pip install pypdf pdfplumber`
2. 检查 PDF 文件是否损坏
3. 查看日志获取详细错误信息

---

## 相关文档

- [Ollama API 文档](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [ChromaDB 文档](https://docs.trychroma.com/)

---

## 联系和支持

如有问题，请查看：
- 后端日志：`/tmp/backend.log`
- 前端日志：`/tmp/frontend.log`
- 项目 README：`README.md`
