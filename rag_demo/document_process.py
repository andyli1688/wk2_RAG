
from __future__ import annotations

from typing import Callable, List

import tiktoken
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_pdf_texts(
    file_path: str,
    *,
    chunk_size: int = 1024,
    chunk_overlap: int = 100,
    length_function: Callable[[str], int] | None = None,
) -> List[str]:
    """
    Load a PDF and split into text chunks using LangChain.

    Returns: List[str] (each item is a chunk of text)
    """
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    textsplit = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=length_function or num_tokens_from_string,
    )
    chunks = textsplit.split_documents(pages)
    return [c.page_content for c in chunks if c.page_content]
            
def num_tokens_from_string(string):   
    encoding = tiktoken.get_encoding('cl100k_base')
    num_tokens = len(encoding.encode(string))
    return num_tokens



if __name__ == '__main__':
    texts = chunk_pdf_texts('Speech and Language Processing.pdf')
    print(f"Chunks: {len(texts)}\n")
    for i, chunk in enumerate(texts):
        print(f"Chunk {i+1}:\n{chunk}\n{'='*40}\n")