#!/bin/bash

# RAG Demo 环境设置脚本
# 使用方法: bash setup.sh

echo "=========================================="
echo "RAG Demo 环境设置"
echo "=========================================="

# 检查 Python 版本
echo ""
echo "1. 检查 Python 版本..."
python3 --version

if [ $? -ne 0 ]; then
    echo "错误: 未找到 Python 3，请先安装 Python 3.8 或更高版本"
    exit 1
fi

# 创建虚拟环境
echo ""
echo "2. 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 虚拟环境已创建"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "3. 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo ""
echo "4. 升级 pip..."
pip install --upgrade pip

# 安装依赖
echo ""
echo "5. 安装依赖包..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ 环境设置完成！"
    echo "=========================================="
    echo ""
    echo "下一步："
    echo "1. 确保已设置 OPENAI_API_KEY 环境变量"
    echo "2. 运行应用: streamlit run app.py"
    echo ""
    echo "或者运行: bash run.sh"
    echo ""
else
    echo ""
    echo "错误: 依赖安装失败，请检查错误信息"
    exit 1
fi
