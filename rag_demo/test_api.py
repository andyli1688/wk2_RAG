#!/usr/bin/env python3
"""
API 测试脚本 - Python 版本
用于测试后端 REST API 和验证 Ollama API 调用
"""

import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def print_success(message):
    """打印成功消息"""
    print(f"✓ {message}")

def print_error(message):
    """打印错误消息"""
    print(f"✗ {message}")

def print_warning(message):
    """打印警告消息"""
    print(f"⚠ {message}")

def test_ollama():
    """测试 Ollama 服务"""
    print_section("1. 测试 Ollama 服务")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print_success("Ollama 服务运行正常")
            print(f"已安装的模型数量: {len(models)}")
            for model in models[:5]:  # 只显示前5个
                print(f"  - {model.get('name', 'Unknown')}")
            return True
        else:
            print_error(f"Ollama 服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到 Ollama 服务")
        print("请确保 Ollama 正在运行: ollama serve")
        return False
    except Exception as e:
        print_error(f"测试 Ollama 时出错: {e}")
        return False

def test_backend_health():
    """测试后端健康检查"""
    print_section("2. 测试后端健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("后端服务运行正常")
            print(f"状态: {data.get('status')}")
            print(f"向量数据库存在: {data.get('chroma_db_exists')}")
            print(f"集合存在: {data.get('collection_exists')}")
            print(f"文档块数量: {data.get('collection_count', 0)}")
            return True
        else:
            print_error(f"后端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到后端服务")
        print("请确保后端服务正在运行: cd backend && uvicorn main:app --reload")
        return False
    except Exception as e:
        print_error(f"测试后端服务时出错: {e}")
        return False

def test_root_endpoint():
    """测试根端点"""
    print_section("3. 测试根端点")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("根端点正常")
            print(f"消息: {data.get('message')}")
            print(f"版本: {data.get('version')}")
            print("可用端点:")
            for endpoint, path in data.get('endpoints', {}).items():
                print(f"  - {endpoint}: {path}")
            return True
        else:
            print_error(f"根端点响应异常: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"测试根端点时出错: {e}")
        return False

def test_check_index():
    """测试向量数据库检查"""
    print_section("4. 测试向量数据库检查")
    try:
        response = requests.post(f"{BASE_URL}/api/check_and_index", timeout=300)
        if response.status_code == 200:
            data = response.json()
            print_success("向量数据库检查完成")
            print(f"已索引: {data.get('indexed')}")
            print(f"消息: {data.get('message')}")
            print(f"文档块数量: {data.get('count', 0)}")
            return True
        else:
            print_error(f"向量数据库检查失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print_warning("向量数据库检查超时（可能需要较长时间）")
        return False
    except Exception as e:
        print_error(f"测试向量数据库检查时出错: {e}")
        return False

def test_upload_report():
    """测试上传报告"""
    print_section("5. 测试上传报告")
    
    # 查找测试 PDF 文件
    test_pdf = None
    for path in ["storage/reports", "uploads"]:
        pdf_dir = Path(path)
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            if pdf_files:
                test_pdf = pdf_files[0]
                break
    
    if not test_pdf:
        print_warning("未找到测试 PDF 文件，跳过上传测试")
        print("提示: 将 PDF 文件放在 storage/reports/ 或 uploads/ 目录")
        return None
    
    print(f"使用测试文件: {test_pdf}")
    try:
        with open(test_pdf, "rb") as f:
            files = {"file": (test_pdf.name, f, "application/pdf")}
            response = requests.post(
                f"{BASE_URL}/api/upload_report",
                files=files,
                timeout=120
            )
        
        if response.status_code == 200:
            data = response.json()
            print_success("上传成功")
            print(f"报告ID: {data.get('report_id')}")
            print(f"提取的论点数量: {len(data.get('claims', []))}")
            print(f"消息: {data.get('message')}")
            
            # 显示前3个论点
            claims = data.get('claims', [])[:3]
            if claims:
                print("\n前3个论点:")
                for claim in claims:
                    print(f"  - {claim.get('claim_id')}: {claim.get('claim_text', '')[:50]}...")
            
            return data.get('report_id')
        else:
            print_error(f"上传失败: {response.status_code}")
            print(f"响应: {response.text}")
            return None
    except Exception as e:
        print_error(f"测试上传时出错: {e}")
        return None

def test_analyze(report_id):
    """测试分析报告"""
    print_section("6. 测试分析报告")
    
    if not report_id:
        print_warning("未提供 report_id，跳过分析测试")
        return False
    
    print(f"使用 Report ID: {report_id}")
    payload = {
        "report_id": report_id,
        "top_k": 3,
        "max_claims": 5
    }
    
    try:
        print("正在分析（这可能需要几分钟）...")
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=payload,
            timeout=1800  # 30分钟超时
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("分析成功")
            
            report = data.get('report', {})
            summary = report.get('summary', {})
            
            print("\n分析摘要:")
            print(f"  总论点: {summary.get('total_claims', 0)}")
            print(f"  完全解决: {summary.get('fully_addressed', 0)}")
            print(f"  部分解决: {summary.get('partially_addressed', 0)}")
            print(f"  未解决: {summary.get('not_addressed', 0)}")
            print(f"  平均置信度: {summary.get('average_confidence', 0):.1f}%")
            
            # 显示第一个论点的分析
            claim_analyses = report.get('claim_analyses', [])
            if claim_analyses:
                first_analysis = claim_analyses[0]
                print(f"\n第一个论点分析 ({first_analysis.get('claim_id')}):")
                print(f"  覆盖情况: {first_analysis.get('coverage')}")
                print(f"  置信度: {first_analysis.get('confidence')}%")
                print(f"  引用数量: {len(first_analysis.get('citations', []))}")
            
            return True
        else:
            print_error(f"分析失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print_warning("分析超时（可能需要更长时间）")
        return False
    except Exception as e:
        print_error(f"测试分析时出错: {e}")
        return False

def main():
    """主测试流程"""
    print("\n" + "=" * 50)
    print("API 测试脚本")
    print("=" * 50)
    
    results = {
        "ollama": test_ollama(),
        "backend_health": test_backend_health(),
        "root": test_root_endpoint(),
        "check_index": test_check_index(),
    }
    
    report_id = test_upload_report()
    if report_id:
        results["analyze"] = test_analyze(report_id)
    
    # 总结
    print_section("测试总结")
    print(f"Ollama 服务: {'✓' if results.get('ollama') else '✗'}")
    print(f"后端健康检查: {'✓' if results.get('backend_health') else '✗'}")
    print(f"根端点: {'✓' if results.get('root') else '✗'}")
    print(f"向量数据库检查: {'✓' if results.get('check_index') else '✗'}")
    if 'analyze' in results:
        print(f"分析测试: {'✓' if results.get('analyze') else '✗'}")
    
    print("\n" + "=" * 50)
    print("访问以下地址查看 API 文档:")
    print(f"  - Swagger UI: {BASE_URL}/docs")
    print(f"  - ReDoc: {BASE_URL}/redoc")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
