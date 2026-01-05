#!/bin/bash

# RAG Demo 运行脚本
# 使用方法: bash run.sh

echo "=========================================="
echo "启动 RAG Demo 应用"
echo "=========================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境不存在，请先运行: bash setup.sh"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 检查环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "⚠️  警告: 未设置 OPENAI_API_KEY 环境变量"
    echo "请设置: export OPENAI_API_KEY='your-api-key'"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查嵌入服务配置
echo "检查配置..."
echo "嵌入服务 URL: http://test.2brain.cn:9800/v1/emb"
echo ""

# 创建必要的目录
mkdir -p uploads
mkdir -p faiss_out

# 运行 Streamlit 应用
echo "启动 Streamlit 应用..."
echo "应用将在浏览器中自动打开: http://localhost:8501"
echo ""
streamlit run app.py
