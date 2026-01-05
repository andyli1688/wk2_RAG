# RAG 问答助手 - Streamlit 应用

基于 Streamlit 的 RAG（检索增强生成）问答系统，支持文档上传、向量检索和智能问答。

## 功能特性

✅ **文档上传**: 支持 PDF 文档上传，显示上传进度和处理状态  
✅ **文档处理**: 自动进行文档解析、文本分块、向量化，并构建 FAISS 索引  
✅ **问题输入**: 简洁的问题输入界面，支持自定义检索数量  
✅ **检索和生成**: 显示加载状态，进行向量检索和答案生成  
✅ **答案显示**: 展示生成的答案，并提供来源引用和相关文档片段  

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址：`http://localhost:8501`

## 使用说明

### 1. 上传文档

- 在左侧边栏的"文档管理"区域，点击"上传 PDF 文档"
- 选择要处理的 PDF 文件
- 点击"🚀 处理文档"按钮开始处理

### 2. 文档处理流程

系统会自动执行以下步骤：
1. **文档解析**: 从 PDF 中提取文本内容
2. **文本分块**: 将文档分割成适合处理的文本块
3. **向量化**: 使用嵌入服务将文本转换为向量
4. **构建索引**: 使用 FAISS 构建向量索引并保存

处理过程中会显示实时进度和状态信息。

### 3. 提问和回答

- 在主页面的问题输入框中输入您的问题
- 可以调整"检索文档数量"滑块（默认 10 个）
- 点击"🔍 提交"按钮
- 系统会：
  - 检索相关文档片段
  - 基于检索结果生成答案
  - 显示答案和相关文档片段

### 4. 查看来源

答案下方会显示相关的文档片段，每个片段包含：
- 相似度分数
- 完整的文本内容

## 配置说明

### 嵌入服务

默认使用 `http://test.2brain.cn:9800/v1/emb` 作为嵌入服务。如需修改，请编辑 `embedding.py` 中的 `EMBEDDING_URL`。

### OpenAI API

需要设置 OpenAI API Key 环境变量：
```bash
export OPENAI_API_KEY="your-api-key"
```

或在代码中直接配置（不推荐用于生产环境）。

### 索引存储

- 索引文件保存在 `faiss_out/` 目录
- 上传的文件保存在 `uploads/` 目录
- 这些目录会在首次运行时自动创建

## 项目结构

```
rag_demo/
├── app.py                 # Streamlit 主应用
├── document_process.py    # 文档处理模块
├── embedding.py           # 向量嵌入模块
├── faiss_demo.py         # FAISS 索引管理
├── generation.py         # 答案生成模块
├── requirements.txt      # 依赖列表
├── uploads/             # 上传文件目录
└── faiss_out/           # 索引文件目录
```

## 注意事项

1. **首次运行**: 需要先上传并处理至少一个文档才能进行问答
2. **文件大小**: 建议上传的 PDF 文件不要过大，以免处理时间过长
3. **网络连接**: 确保能够访问嵌入服务和 OpenAI API
4. **API 费用**: 使用 OpenAI API 会产生费用，请注意使用量

## 故障排除

### 嵌入服务连接失败
- 检查 `embedding.py` 中的 `EMBEDDING_URL` 是否正确
- 确认网络连接正常

### OpenAI API 错误
- 检查 API Key 是否正确设置
- 确认账户有足够的额度

### 索引加载失败
- 删除 `faiss_out/` 目录重新处理文档
- 检查文件权限

## 开发说明

应用使用 Streamlit 的 session state 来管理状态：
- `st.session_state.index`: FAISS 索引对象
- `st.session_state.meta`: 文档元数据
- `st.session_state.processed_files`: 已处理文件列表
- `st.session_state.qa_history`: 问答历史记录
