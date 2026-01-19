"""
Streamlit UI for Short Report Rebuttal Assistant
"""
import os
import sys
from pathlib import Path
import requests
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import OLLAMA_BASE_URL, LLM_MODEL, EMBED_MODEL

# Page configuration
st.set_page_config(
    page_title="空头报告反驳助手",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "report_id" not in st.session_state:
    st.session_state.report_id = None
if "claims" not in st.session_state:
    st.session_state.claims = []
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

# Title
st.title("📊 空头报告反驳助手")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ 配置")
    
    # API URL
    api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        help="FastAPI后端地址"
    )
    st.session_state.api_url = api_url
    
    # Test connection
    if st.button("🔌 测试连接", use_container_width=True):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                st.success("✓ 连接成功!")
                st.json(health)
            else:
                st.error("连接失败")
        except Exception as e:
            st.error(f"连接错误: {e}")
    
    st.markdown("---")
    st.header("📚 说明")
    st.markdown("""
    1. **上传报告**: 上传空头报告PDF文件（仅处理前3页）
    2. **提取论点**: 系统自动提取独立论点
    3. **分析**: 对每个论点进行检索和判断
    4. **下载报告**: 下载Markdown或JSON格式的分析报告
    """)

# Main content
tab1, tab2, tab3 = st.tabs(["📤 上传报告", "🔍 分析", "📥 下载报告"])

# Tab 1: Upload Report
with tab1:
    st.header("上传空头报告")
    
    uploaded_file = st.file_uploader(
        "选择PDF文件",
        type=["pdf"],
        help="仅处理前3页内容"
    )
    
    if uploaded_file is not None:
        if st.button("🚀 上传并提取论点", type="primary", use_container_width=True):
            with st.spinner("正在上传和处理报告..."):
                try:
                    # Upload file
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(
                        f"{st.session_state.api_url}/upload_report",
                        files=files,
                        timeout=300
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    st.session_state.report_id = result["report_id"]
                    st.session_state.claims = result["claims"]
                    
                    st.success(f"✓ 成功上传! 提取了 {len(result['claims'])} 个论点")
                    
                    # Display claims
                    st.subheader("提取的论点")
                    for i, claim in enumerate(result["claims"], 1):
                        with st.expander(f"{claim['claim_id']}: {claim['claim_text'][:100]}..."):
                            st.write(f"**类型**: {claim['claim_type']}")
                            st.write(f"**页码**: {', '.join(map(str, claim['page_numbers']))}")
                            st.write(f"**内容**: {claim['claim_text']}")
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"上传失败: {e}")
                    st.info("请确保FastAPI服务正在运行: `uvicorn main:app --reload`")
                except Exception as e:
                    st.error(f"处理失败: {e}")

# Tab 2: Analyze
with tab2:
    st.header("分析论点")
    
    if not st.session_state.report_id:
        st.info("👈 请先上传报告")
    else:
        st.info(f"当前报告ID: `{st.session_state.report_id}`")
        
        col1, col2 = st.columns(2)
        with col1:
            top_k = st.slider("检索文档数量", min_value=3, max_value=20, value=6, step=1)
        with col2:
            max_claims = st.slider("最大分析论点数", min_value=5, max_value=50, value=30, step=1)
        
        if st.button("🔍 开始分析", type="primary", use_container_width=True):
            with st.spinner("正在分析论点，这可能需要几分钟..."):
                try:
                    payload = {
                        "report_id": st.session_state.report_id,
                        "top_k": top_k,
                        "max_claims": max_claims
                    }
                    
                    # Use a longer timeout and handle connection errors
                    try:
                        response = requests.post(
                            f"{st.session_state.api_url}/analyze",
                            json=payload,
                            timeout=(30, 1800)  # (connect timeout, read timeout) - 30s connect, 30min read
                        )
                    except requests.exceptions.ConnectionError as e:
                        st.error(f"连接错误: {e}")
                        st.info("分析过程可能需要较长时间，请稍后重试。如果问题持续，请检查服务器日志。")
                        st.stop()
                    except requests.exceptions.Timeout as e:
                        st.error(f"请求超时: 分析过程超过30分钟")
                        st.info("请尝试减少分析的论点数或稍后重试。")
                        st.stop()
                    response.raise_for_status()
                    
                    result = response.json()
                    st.session_state.analysis = result["report"]
                    
                    st.success("✓ 分析完成!")
                    
                    # Display summary
                    summary = result["report"]["summary"]
                    st.subheader("执行摘要")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总论点", summary["total_claims"])
                    with col2:
                        st.metric("完全解决", summary["fully_addressed"], 
                                 delta=f"{summary['fully_addressed']/summary['total_claims']*100:.1f}%")
                    with col3:
                        st.metric("部分解决", summary["partially_addressed"],
                                 delta=f"{summary['partially_addressed']/summary['total_claims']*100:.1f}%")
                    with col4:
                        st.metric("未解决", summary["not_addressed"],
                                 delta=f"{summary['not_addressed']/summary['total_claims']*100:.1f}%")
                    
                    st.metric("平均置信度", f"{summary['average_confidence']}/100")
                    
                    # Key gaps
                    if summary.get("key_gaps"):
                        st.subheader("主要证据缺口")
                        for gap in summary["key_gaps"]:
                            st.write(f"- {gap}")
                    
                    # Priority actions
                    if summary.get("priority_actions"):
                        st.subheader("优先行动建议")
                        for action in summary["priority_actions"]:
                            st.write(f"- {action}")
                    
                    # Detailed analyses
                    st.subheader("详细分析")
                    analyses = result["report"]["claim_analyses"]
                    
                    # Filter by coverage
                    coverage_filter = st.selectbox(
                        "筛选覆盖情况",
                        ["全部", "完全解决", "部分解决", "未解决"]
                    )
                    
                    filtered_analyses = analyses
                    if coverage_filter == "完全解决":
                        filtered_analyses = [a for a in analyses if a["coverage"] == "fully_addressed"]
                    elif coverage_filter == "部分解决":
                        filtered_analyses = [a for a in analyses if a["coverage"] == "partially_addressed"]
                    elif coverage_filter == "未解决":
                        filtered_analyses = [a for a in analyses if a["coverage"] == "not_addressed"]
                    
                    for analysis in filtered_analyses:
                        # Find corresponding claim
                        claim = next((c for c in st.session_state.claims if c["claim_id"] == analysis["claim_id"]), None)
                        
                        coverage_icon = {
                            "fully_addressed": "✅",
                            "partially_addressed": "⚠️",
                            "not_addressed": "❌"
                        }.get(analysis["coverage"], "❓")
                        
                        with st.expander(f"{coverage_icon} {analysis['claim_id']}: {claim['claim_text'][:80] if claim else 'Unknown'}..."):
                            st.write(f"**覆盖情况**: {analysis['coverage']}")
                            st.write(f"**置信度**: {analysis['confidence']}/100")
                            st.write(f"**分析**:\n{analysis['reasoning']}")
                            
                            if analysis.get("citations"):
                                st.write("**引用来源**:")
                                for cit in analysis["citations"]:
                                    st.write(f"- {cit['doc_title']} (分块: {cit['chunk_id']})")
                                    st.write(f"  > {cit['quote'][:200]}...")
                            
                            if analysis.get("gaps"):
                                st.write("**证据缺口**:")
                                for gap in analysis["gaps"]:
                                    st.write(f"- {gap}")
                            
                            if analysis.get("recommended_actions"):
                                st.write("**建议行动**:")
                                for action in analysis["recommended_actions"]:
                                    st.write(f"- {action}")
                
                except requests.exceptions.RequestException as e:
                    st.error(f"分析失败: {e}")
                except Exception as e:
                    st.error(f"处理失败: {e}")

# Tab 3: Download
with tab3:
    st.header("下载报告")
    
    if not st.session_state.report_id:
        st.info("👈 请先上传并分析报告")
    else:
        st.info(f"当前报告ID: `{st.session_state.report_id}`")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 下载Markdown报告", use_container_width=True):
                try:
                    response = requests.get(
                        f"{st.session_state.api_url}/download_report/{st.session_state.report_id}?format=md",
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    st.download_button(
                        label="⬇️ 保存Markdown文件",
                        data=response.content,
                        file_name=f"report_{st.session_state.report_id}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"下载失败: {e}")
        
        with col2:
            if st.button("📋 下载JSON报告", use_container_width=True):
                try:
                    response = requests.get(
                        f"{st.session_state.api_url}/download_report/{st.session_state.report_id}?format=json",
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    st.download_button(
                        label="⬇️ 保存JSON文件",
                        data=response.content,
                        file_name=f"report_{st.session_state.report_id}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"下载失败: {e}")
        
        # Display markdown preview
        if st.session_state.analysis:
            st.subheader("报告预览 (Markdown)")
            st.markdown(st.session_state.analysis["markdown"][:5000] + "...")
