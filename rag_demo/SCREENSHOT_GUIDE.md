# 截图指南 - 验证 API 正常工作

本文档说明需要截取哪些截图来证明大模型 API 和后端 REST API 都能正常工作。

## 截图清单

### 1. Ollama API 验证截图

#### 1.1 检查 Ollama 服务运行状态

**命令**:
```bash
curl http://localhost:11434/api/tags
```

**截图内容**:
- 终端显示已安装的模型列表
- 应该看到 `llama3.1:8b` 和 `nomic-embed-text` 模型

**示例输出**:
```json
{
  "models": [
    {
      "name": "llama3.1:8b",
      "modified_at": "2024-01-24T...",
      "size": 4723888128
    },
    {
      "name": "nomic-embed-text",
      "modified_at": "2024-01-24T...",
      "size": 274832896
    }
  ]
}
```

#### 1.2 测试 Ollama Chat API

**命令**:
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}'
```

**截图内容**:
- 终端显示 API 调用成功
- 显示模型返回的响应

### 2. 后端 REST API 验证截图

#### 2.1 Swagger UI 主页面

**访问**: `http://localhost:8000/docs`

**截图内容**:
- 浏览器显示 Swagger UI 界面
- 显示所有可用的 API 端点列表
- 包括：`/health`, `/api/upload_report`, `/api/analyze`, `/api/check_and_index`, `/api/download_report/{report_id}`

#### 2.2 健康检查端点测试

**在 Swagger UI 中**:
1. 点击 `GET /health` 端点
2. 点击 "Try it out"
3. 点击 "Execute"

**截图内容**:
- Swagger UI 显示请求和响应
- 响应应该包含：
  ```json
  {
    "status": "healthy",
    "chroma_db_exists": true,
    "collection_exists": true,
    "collection_count": 150
  }
  ```

#### 2.3 上传报告端点测试

**在 Swagger UI 中**:
1. 点击 `POST /api/upload_report` 端点
2. 点击 "Try it out"
3. 选择 PDF 文件
4. 点击 "Execute"

**截图内容**:
- Swagger UI 显示文件上传界面
- 显示成功响应，包含 `report_id` 和 `claims` 列表

#### 2.4 分析端点测试

**在 Swagger UI 中**:
1. 点击 `POST /api/analyze` 端点
2. 点击 "Try it out"
3. 输入之前获取的 `report_id`
4. 设置 `top_k` 和 `max_claims`
5. 点击 "Execute"

**截图内容**:
- Swagger UI 显示请求参数
- 显示分析结果，包含：
  - `summary`（摘要统计）
  - `claim_analyses`（每个论点的详细分析）
  - `markdown` 和 `json` 格式的报告

#### 2.5 使用 curl 测试 API

**终端截图**:

**测试健康检查**:
```bash
curl http://localhost:8000/health | jq
```

**测试上传**:
```bash
curl -X POST http://localhost:8000/api/upload_report \
  -F "file=@test_report.pdf" | jq
```

**测试分析**:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"report_id": "xxx", "top_k": 6, "max_claims": 30}' | jq
```

**截图内容**:
- 终端显示命令执行
- 显示 JSON 格式的响应结果

### 3. 测试脚本运行截图

#### 3.1 运行 Shell 测试脚本

**命令**:
```bash
./test_api.sh
```

**截图内容**:
- 终端显示测试进度
- 显示每个测试步骤的结果（✓ 或 ✗）
- 显示最终的测试总结

#### 3.2 运行 Python 测试脚本

**命令**:
```bash
python test_api.py
```

**截图内容**:
- 终端显示详细的测试输出
- 显示每个 API 端点的测试结果
- 显示分析摘要和统计信息

### 4. 前端界面截图

#### 4.1 前端主界面

**访问**: `http://localhost:3000`

**截图内容**:
- 浏览器显示前端主界面
- 显示三个标签页：上传报告、分析、下载报告
- 显示向量数据库状态

#### 4.2 上传报告界面

**截图内容**:
- 显示文件上传区域
- 上传成功后显示提取的论点列表

#### 4.3 分析结果界面

**截图内容**:
- 显示分析摘要统计（总论点、完全解决、部分解决、未解决）
- 显示每个论点的详细分析
- 显示检索到的证据文档列表
- 显示相似度分数和引用文本

### 5. 后端日志截图

#### 5.1 查看后端日志

**命令**:
```bash
tail -f /tmp/backend.log
```

**截图内容**:
- 显示 API 请求日志
- 显示 Ollama API 调用日志
- 显示向量数据库操作日志
- 显示错误信息（如果有）

#### 5.2 关键日志条目

**需要截取的日志内容**:
- "Starting internal document indexing"
- "Calling Ollama API with model: llama3.1:8b"
- "Retrieved X relevant documents"
- "Successfully indexed X chunks"
- "Generated report for {report_id}"

### 6. 完整工作流程截图序列

**建议的截图顺序**:

1. **启动服务**
   - 显示 `./run.sh` 启动输出
   - 显示服务运行状态

2. **检查向量数据库**
   - 前端显示向量数据库状态
   - 或运行 `curl -X POST http://localhost:8000/api/check_and_index`

3. **上传报告**
   - Swagger UI 或前端界面上传 PDF
   - 显示提取的论点列表

4. **分析报告**
   - 显示分析进度
   - 显示分析结果摘要

5. **查看详细分析**
   - 显示每个论点的分析
   - 显示检索到的证据文档

6. **下载报告**
   - 显示下载的 Markdown 或 JSON 报告

## 截图工具推荐

- **macOS**: `Cmd + Shift + 4` (选择区域截图)
- **Linux**: `gnome-screenshot` 或 `scrot`
- **Windows**: `Win + Shift + S`

## 截图命名建议

建议使用以下命名格式：
- `01_ollama_models.png` - Ollama 模型列表
- `02_swagger_ui.png` - Swagger UI 主页面
- `03_health_check.png` - 健康检查结果
- `04_upload_report.png` - 上传报告结果
- `05_analyze_result.png` - 分析结果
- `06_frontend_analysis.png` - 前端分析界面
- `07_backend_logs.png` - 后端日志

## 验证要点

确保截图能够证明：

1. ✅ Ollama 服务正常运行
2. ✅ 后端 REST API 服务正常运行
3. ✅ 所有 API 端点都能正常响应
4. ✅ 能够成功调用 Ollama LLM API 提取论点
5. ✅ 能够成功调用 Ollama Embedding API 生成向量
6. ✅ 能够成功从向量数据库检索文档
7. ✅ 能够成功生成完整的分析报告
8. ✅ 前端能够正常调用后端 API
9. ✅ 错误处理正常工作（如果有错误）

## 示例截图说明文字

为每张截图添加说明文字，例如：

**图1: Ollama 服务状态**
- 显示已安装的模型：llama3.1:8b 和 nomic-embed-text
- 证明 Ollama API 服务正常运行

**图2: Swagger UI - API 端点列表**
- 显示所有可用的 REST API 端点
- 证明后端服务正常运行

**图3: 健康检查响应**
- 显示服务状态为 "healthy"
- 显示向量数据库存在且有 150 个文档块

**图4: 上传报告响应**
- 显示成功提取了 15 个论点
- 显示每个论点的 ID、文本和类型

**图5: 分析结果摘要**
- 显示 8 个完全解决、5 个部分解决、2 个未解决
- 显示平均置信度为 75.5%

**图6: 前端分析界面**
- 显示每个论点的详细分析
- 显示检索到的证据文档和相似度分数

---

## 快速测试命令

运行以下命令快速验证所有 API：

```bash
# 1. 测试 Ollama
curl http://localhost:11434/api/tags

# 2. 测试后端健康检查
curl http://localhost:8000/health

# 3. 运行完整测试脚本
./test_api.sh
```

所有测试通过后，即可截图证明 API 正常工作。
