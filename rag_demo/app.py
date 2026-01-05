"""
Streamlit RAG 问答应用
整合文档上传、处理、向量检索和答案生成功能
"""

import os
import tempfile
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
import streamlit as st
from openai import OpenAI

from document_process import chunk_pdf_texts
from embedding import local_embedding
from faiss_demo import (
    EMBEDDING_DIM,
    DEFAULT_TOP_K,
    create_index,
    load_meta,
    save_meta,
    add_texts,
    search,
    _normalize,
)
from generation import generate_answer

# 页面配置
st.set_page_config(
    page_title="RAG 问答助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 OpenAI 客户端
@st.cache_resource
def get_openai_client():
    return OpenAI()

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUT_DIR = os.path.join(BASE_DIR, "faiss_out")
INDEX_FILE_PATH = os.path.join(OUT_DIR, "rag.index.faiss")
META_FILE_PATH = os.path.join(OUT_DIR, "rag.meta.json")

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# 初始化 session state
if "index" not in st.session_state:
    st.session_state.index = None
if "meta" not in st.session_state:
    st.session_state.meta = {}
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "processing_status" not in st.session_state:
    st.session_state.processing_status = "未开始"


def load_index_if_exists():
    """如果索引文件存在，加载索引和元数据"""
    if os.path.exists(INDEX_FILE_PATH) and os.path.exists(META_FILE_PATH):
        try:
            index = faiss.read_index(INDEX_FILE_PATH)
            meta = load_meta(META_FILE_PATH)
            return index, meta
        except Exception as e:
            st.error(f"加载索引失败: {e}")
            return None, {}
    return None, {}


def process_uploaded_file(uploaded_file) -> Tuple[Optional[faiss.Index], Dict[int, str], str]:
    """
    处理上传的文件：解析、分块、向量化、构建索引
    
    Returns:
        (index, meta, status_message)
    """
    try:
        # 保存上传的文件
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 1. 文档解析和分块
        with st.spinner("正在解析文档..."):
            texts = chunk_pdf_texts(file_path)
            if not texts:
                return None, {}, "错误：未能从文档中提取文本"
        
        st.success(f"✓ 文档解析完成，共提取 {len(texts)} 个文本块")
        
        # 2. 向量化
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 加载或创建索引
        if st.session_state.index is None:
            index = create_index(dim=EMBEDDING_DIM)
            meta = {}
        else:
            index = st.session_state.index
            meta = st.session_state.meta.copy()
        
        # 批量处理向量化
        batch_size = 25
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        status_text.text(f"正在向量化文本块 (0/{len(texts)})...")
        
        vectors = []
        for i, batch_start in enumerate(range(0, len(texts), batch_size)):
            batch = texts[batch_start:batch_start + batch_size]
            try:
                batch_vecs = local_embedding(batch)
                arr = np.asarray(batch_vecs, dtype="float32")
                if arr.ndim != 2 or arr.shape[1] != EMBEDDING_DIM:
                    return None, {}, f"错误：向量维度不匹配，期望 {EMBEDDING_DIM}，得到 {arr.shape[1]}"
                vectors.append(arr)
                
                progress = (i + 1) / total_batches
                progress_bar.progress(progress)
                status_text.text(f"正在向量化文本块 ({min(batch_start + len(batch), len(texts))}/{len(texts)})...")
            except Exception as e:
                return None, {}, f"向量化失败: {e}"
        
        if not vectors:
            return None, {}, "错误：未能生成向量"
        
        vectors_array = np.vstack(vectors).astype("float32", copy=False)
        _normalize(vectors_array)
        
        st.success(f"✓ 向量化完成，共生成 {len(vectors_array)} 个向量")
        
        # 3. 添加到索引
        status_text.text("正在构建 FAISS 索引...")
        start_id = (max(meta.keys()) + 1) if meta else 0
        ids = np.arange(start_id, start_id + len(texts)).astype("int64")
        
        index.add_with_ids(vectors_array, ids)
        for i, t in zip(ids.tolist(), texts):
            meta[i] = t
        
        # 4. 保存索引
        status_text.text("正在保存索引...")
        faiss.write_index(index, INDEX_FILE_PATH)
        save_meta(META_FILE_PATH, meta)
        
        progress_bar.empty()
        status_text.empty()
        
        return index, meta, f"✓ 处理完成！已添加 {len(texts)} 个文本块到索引"
        
    except Exception as e:
        return None, {}, f"处理文件时出错: {e}"


def search_and_answer(question: str, top_k: int = DEFAULT_TOP_K):
    """
    检索相关文档并生成答案
    
    Returns:
        (answer, search_results)
    """
    if st.session_state.index is None or not st.session_state.meta:
        return None, [], "错误：请先上传并处理文档"
    
    # 1. 向量检索
    with st.spinner("正在检索相关文档..."):
        search_results = search(
            index=st.session_state.index,
            meta=st.session_state.meta,
            query=question,
            top_k=top_k
        )
    
    if not search_results:
        return None, [], "未找到相关文档"
    
    # 2. 构建上下文
    context_parts = []
    for i, r in enumerate(search_results, 1):
        context_parts.append(f"[片段 {i}] {r['text']}")
    context = "\n\n".join(context_parts)
    
    # 3. 生成答案
    with st.spinner("正在生成答案..."):
        try:
            client = get_openai_client()
            answer = generate_answer(context_text=context, user_question=question)
            return answer, search_results, None
        except Exception as e:
            return None, search_results, f"生成答案时出错: {e}"


# 主界面
st.title("📚 RAG 问答助手")
st.markdown("---")

# 侧边栏：文档上传和处理
with st.sidebar:
    st.header("📄 文档管理")
    
    # 加载现有索引
    if st.session_state.index is None:
        index, meta = load_index_if_exists()
        if index is not None:
            st.session_state.index = index
            st.session_state.meta = meta
            st.success(f"已加载索引（{index.ntotal} 个向量）")
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "上传 PDF 文档",
        type=["pdf"],
        help="支持上传 PDF 格式的文档"
    )
    
    if uploaded_file is not None:
        if st.button("🚀 处理文档", type="primary", use_container_width=True):
            with st.spinner("正在处理文档..."):
                index, meta, status_msg = process_uploaded_file(uploaded_file)
                
                if index is not None:
                    st.session_state.index = index
                    st.session_state.meta = meta
                    st.session_state.processed_files.append(uploaded_file.name)
                    st.success(status_msg)
                    st.rerun()
                else:
                    st.error(status_msg)
    
    # 显示索引状态
    st.markdown("---")
    st.subheader("索引状态")
    if st.session_state.index is not None:
        st.info(f"**向量数量**: {st.session_state.index.ntotal}\n\n**已处理文件**: {len(st.session_state.processed_files)}")
        if st.session_state.processed_files:
            for fname in st.session_state.processed_files:
                st.text(f"• {fname}")
    else:
        st.warning("尚未创建索引，请上传文档")

# 主内容区：问答界面
if st.session_state.index is None or not st.session_state.meta:
    st.info("👈 请先在左侧上传并处理文档，然后才能进行问答")
else:
    # 问题输入
    st.subheader("💬 提问")
    question = st.text_input(
        "输入您的问题",
        placeholder="例如：解释一下统计语言模型",
        key="question_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        submit_button = st.button("🔍 提交", type="primary", use_container_width=True)
    
    with col2:
        top_k = st.slider("检索文档数量", min_value=3, max_value=20, value=DEFAULT_TOP_K, step=1)
    
    # 初始化历史记录
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []
    
    # 处理问答
    if submit_button and question:
        answer, search_results, error = search_and_answer(question, top_k=top_k)
        
        if error:
            st.error(error)
        elif answer:
            # 保存到历史记录
            st.session_state.qa_history.append({
                "question": question,
                "answer": answer,
                "sources": search_results
            })
            
            # 显示答案
            st.markdown("---")
            st.subheader("📝 答案")
            st.markdown(answer)
            
            # 显示来源引用
            if search_results:
                st.markdown("---")
                st.subheader("📚 相关文档片段")
                
                for i, result in enumerate(search_results, 1):
                    with st.expander(f"片段 {i} (相似度: {result['score']:.4f})"):
                        st.text(result['text'])
        else:
            st.warning("未能生成答案，请检查问题或重试")
    
    # 显示历史问答
    if st.session_state.qa_history:
        st.markdown("---")
        st.subheader("📜 历史问答")
        for qa in reversed(st.session_state.qa_history[-5:]):  # 只显示最近5条
            with st.expander(f"Q: {qa['question']}"):
                st.markdown(f"**A:** {qa['answer']}")
                if qa.get('sources'):
                    st.caption(f"来源: {len(qa['sources'])} 个相关片段")

