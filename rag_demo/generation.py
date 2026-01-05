# Test

"""
生成答案模块：调用 OpenAI API 基于上下文信息回答问题
"""

import os
from openai import OpenAI
import faiss
from faiss_demo import load_meta, search, INDEX_FILE_PATH, META_FILE_PATH, EMBEDDING_DIM, DEFAULT_TOP_K

# 初始化 OpenAI 客户端
client = OpenAI()


def generate_answer(context_text: str, user_question: str, model: str = "gpt-4o", temperature: float = 0.7) -> str:
    """
    基于上下文信息生成答案
    
    Args:
        context_text: 上下文信息（通常是检索到的文档片段）
        user_question: 用户问题
        model: 使用的模型，默认 "gpt-4o"
        temperature: 温度参数，默认 0.7
    
    Returns:
        生成的答案文本
    """
    # 系统提示词
    system_prompt = "你是一个专业的问答助手。请基于提供的上下文信息准确回答用户的问题。"
    
    # 用户提示词模板
    user_prompt = f"""你是一个专业的问答助手。请基于以下上下文信息回答用户的问题。

上下文信息：
{context_text}

用户问题：{user_question}

要求：
1. 只基于提供的上下文信息回答，不要编造信息
2. 如果上下文中没有相关信息，请明确说明
3. 答案要准确、简洁、有条理
4. 可以引用具体的文档来源

请回答："""

    # 调用 OpenAI API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature
    )
    
    answer = response.choices[0].message.content
    return answer


if __name__ == "__main__":
    # 测试示例：从 faiss 检索获取 context
    question = "解释一下SEMANTIC ROLE LABELING"
    
    # 加载 faiss index 和 meta
    if not os.path.exists(INDEX_FILE_PATH) or not os.path.exists(META_FILE_PATH):
        print(f"错误：找不到 index 文件。请先运行 faiss_demo.py 创建索引。")
        print(f"Index 路径: {INDEX_FILE_PATH}")
        print(f"Meta 路径: {META_FILE_PATH}")
    else:
        print("加载 faiss index...")
        index = faiss.read_index(INDEX_FILE_PATH)
        meta = load_meta(META_FILE_PATH)
        
        # 从 faiss 检索相关内容
        print(f"检索问题: {question}")
        search_results = search(index=index, meta=meta, query=question, top_k=DEFAULT_TOP_K)
        
        # 将检索结果合并成 context
        context_parts = []
        for i, r in enumerate(search_results, 1):
            context_parts.append(f"[片段 {i}] {r['text']}")
        context = "\n\n".join(context_parts)
        
        print(f"\n检索到 {len(search_results)} 个相关片段")
        print("\n" + "="*60)
        for i, r in enumerate(search_results, 1):
            print(f"\n[片段 {i}]:\n{r['text']}\n")
        print("="*60)
        
        # 生成答案
        answer = generate_answer(context_text=context, user_question=question)
        
        print("\n问题：", question)
        print("\n答案：", answer)

