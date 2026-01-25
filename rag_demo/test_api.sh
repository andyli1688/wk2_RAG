#!/bin/bash

# API 测试脚本
# 用于测试后端 REST API 和 Ollama API

BASE_URL="http://localhost:8000"
OLLAMA_URL="http://localhost:11434"

echo "=========================================="
echo "API 测试脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}错误: $1 未安装${NC}"
        return 1
    fi
    return 0
}

# 测试 Ollama 服务
test_ollama() {
    echo -e "${YELLOW}1. 测试 Ollama 服务...${NC}"
    if curl -s $OLLAMA_URL/api/tags > /dev/null; then
        echo -e "${GREEN}✓ Ollama 服务运行正常${NC}"
        echo "已安装的模型:"
        curl -s $OLLAMA_URL/api/tags | python3 -m json.tool | grep -A 1 "name" | head -10
    else
        echo -e "${RED}✗ Ollama 服务未运行${NC}"
        echo "请运行: ollama serve"
        return 1
    fi
    echo ""
}

# 测试后端健康检查
test_health() {
    echo -e "${YELLOW}2. 测试后端健康检查...${NC}"
    response=$(curl -s $BASE_URL/health)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 后端服务运行正常${NC}"
        echo "$response" | python3 -m json.tool
    else
        echo -e "${RED}✗ 后端服务未运行${NC}"
        echo "请运行: cd backend && uvicorn main:app --reload"
        return 1
    fi
    echo ""
}

# 测试根端点
test_root() {
    echo -e "${YELLOW}3. 测试根端点...${NC}"
    response=$(curl -s $BASE_URL/)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 根端点正常${NC}"
        echo "$response" | python3 -m json.tool
    else
        echo -e "${RED}✗ 根端点失败${NC}"
        return 1
    fi
    echo ""
}

# 测试向量数据库检查
test_check_index() {
    echo -e "${YELLOW}4. 测试向量数据库检查...${NC}"
    response=$(curl -s -X POST $BASE_URL/api/check_and_index)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 向量数据库检查完成${NC}"
        echo "$response" | python3 -m json.tool
    else
        echo -e "${RED}✗ 向量数据库检查失败${NC}"
        return 1
    fi
    echo ""
}

# 测试上传报告（如果有测试文件）
test_upload() {
    echo -e "${YELLOW}5. 测试上传报告...${NC}"
    
    # 查找测试 PDF 文件
    TEST_PDF=""
    if [ -f "storage/reports"/*.pdf ]; then
        TEST_PDF=$(ls storage/reports/*.pdf | head -1)
    elif [ -f "uploads"/*.pdf ]; then
        TEST_PDF=$(ls uploads/*.pdf | head -1)
    fi
    
    if [ -z "$TEST_PDF" ]; then
        echo -e "${YELLOW}⚠ 未找到测试 PDF 文件，跳过上传测试${NC}"
        echo "提示: 将 PDF 文件放在 storage/reports/ 或 uploads/ 目录"
        return 0
    fi
    
    echo "使用测试文件: $TEST_PDF"
    response=$(curl -s -X POST $BASE_URL/api/upload_report -F "file=@$TEST_PDF")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 上传成功${NC}"
        echo "$response" | python3 -m json.tool
        
        # 提取 report_id
        REPORT_ID=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['report_id'])" 2>/dev/null)
        if [ ! -z "$REPORT_ID" ]; then
            echo "Report ID: $REPORT_ID"
            echo "$REPORT_ID" > /tmp/test_report_id.txt
        fi
    else
        echo -e "${RED}✗ 上传失败${NC}"
        return 1
    fi
    echo ""
}

# 测试分析（如果有 report_id）
test_analyze() {
    echo -e "${YELLOW}6. 测试分析报告...${NC}"
    
    if [ ! -f "/tmp/test_report_id.txt" ]; then
        echo -e "${YELLOW}⚠ 未找到 report_id，跳过分析测试${NC}"
        echo "提示: 先运行上传测试"
        return 0
    fi
    
    REPORT_ID=$(cat /tmp/test_report_id.txt)
    echo "使用 Report ID: $REPORT_ID"
    
    payload="{\"report_id\": \"$REPORT_ID\", \"top_k\": 3, \"max_claims\": 5}"
    response=$(curl -s -X POST $BASE_URL/api/analyze \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 分析成功${NC}"
        # 只显示摘要部分
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'report' in data and 'summary' in data['report']:
    print(json.dumps(data['report']['summary'], indent=2, ensure_ascii=False))
" 2>/dev/null || echo "$response" | python3 -m json.tool | head -30
    else
        echo -e "${RED}✗ 分析失败${NC}"
        return 1
    fi
    echo ""
}

# 主测试流程
main() {
    check_command curl || exit 1
    check_command python3 || exit 1
    
    test_ollama
    test_health
    test_root
    test_check_index
    test_upload
    test_analyze
    
    echo "=========================================="
    echo -e "${GREEN}测试完成！${NC}"
    echo "=========================================="
    echo ""
    echo "访问以下地址查看 API 文档:"
    echo "  - Swagger UI: $BASE_URL/docs"
    echo "  - ReDoc: $BASE_URL/redoc"
}

main
