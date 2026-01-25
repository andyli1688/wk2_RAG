# 空头报告反驳助手 - 后端

FastAPI 后端服务

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 到 `.env` 并编辑配置：

```bash
cp .env.example .env
```

## 运行服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 将在 http://localhost:8000 运行

API 文档: http://localhost:8000/docs
