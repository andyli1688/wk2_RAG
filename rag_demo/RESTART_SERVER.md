# 重启服务器说明

## 问题已修复

已修复模型名称配置问题：
- 旧配置: `llama3.1` (不存在)
- 新配置: `llama3.1:8b` (已安装)

## 重启FastAPI服务器

由于配置已更改，需要重启FastAPI服务器：

### 方法1: 如果服务器在终端运行
1. 找到运行 `uvicorn main:app --reload` 的终端
2. 按 `Ctrl+C` 停止服务器
3. 重新运行: `uvicorn main:app --reload`

### 方法2: 如果服务器在后台运行
```bash
# 查找进程
ps aux | grep "uvicorn main:app"

# 停止进程（替换PID为实际进程ID）
kill <PID>

# 重新启动
cd /Users/andyli/projects/galaxy_test/wk2_RAG/rag_demo
uvicorn main:app --reload
```

## 验证修复

重启后，再次尝试上传PDF文件。如果仍有问题，请检查：
1. Ollama是否运行: `curl http://localhost:11434/api/tags`
2. 模型是否可用: `ollama list | grep llama3.1`
3. FastAPI日志中的错误信息
