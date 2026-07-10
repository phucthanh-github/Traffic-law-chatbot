import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from langchain_core.documents import Document 
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

# --- 1. SETUP VECTOR DB ---
def setup_vector_db():
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"---Using device for embeddings: {device}---")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": device}
    )
    db_path = "./chroma_db_pdf_v4"
    if os.path.exists(db_path):
        return Chroma(persist_directory=db_path, embedding_function=embeddings).as_retriever(search_kwargs={"k": 15})
    
    # Khởi tạo DB từ các file PDF gốc
    print("---KHOI TAO CHROMA DB TU FILE PDF---")
    import re
    from pypdf import PdfReader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    pdf_files = [
        {"file": "Luật đường bộ.pdf", "name": "Luật Đường bộ số 35/2024/QH15"},
        {"file": "Luật trật tự, an toàn giao thông đường bộ.pdf", "name": "Luật Trật tự an toàn giao thông đường bộ số 36/2024/QH15"},
        {"file": "nghị định 168.pdf", "name": "Nghị định số 168/2024/NĐ-CP (Xử phạt vi phạm hành chính)"}
    ]
    
    docs = []
    for pdf_info in pdf_files:
        filepath = pdf_info["file"]
        doc_name = pdf_info["name"]
        
        if not os.path.exists(filepath):
            print(f"Canh bao: Khong tim thay file {filepath}")
            continue
            
        print(f"Dang doc: {filepath}...")
        reader = PdfReader(filepath)
        full_text = ""
        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n--- TRANG {idx+1} ---\n" + text
                
        # Phân tích theo Điều
        pattern = r'(?=\nĐiều\s+\d+)'
        parts = re.split(pattern, full_text)
        
        current_chapter = "Không rõ"
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # Lấy Chương hiện tại nếu có xuất hiện Chương mới trước Điều
            chapter_matches = re.findall(r'(?:Chương\s+[I|V|X|L|C|D|M\d]+.*?)(?=\n|\Z)', part, re.IGNORECASE)
            if chapter_matches:
                current_chapter = chapter_matches[-1].strip()
                
            if part.startswith("Điều"):
                first_line = part.split("\n")[0]
                article_match = re.match(r'Điều\s+(\d+)[\.:\s]+(.*)', first_line)
                
                if article_match:
                    art_num = article_match.group(1)
                    art_name = article_match.group(2).strip()
                    
                    docs.append(Document(
                        page_content=part,
                        metadata={
                            "source_document": doc_name,
                            "chapter": current_chapter,
                            "article_title": f"Điều {art_num}.",
                            "article_name": art_name
                        }
                    ))
                    
    if not docs:
        raise FileNotFoundError("Khong tim thay hoac khong the doc duoc noi dung tu cac file PDF.")
        
    print(f"Da trich xuat tong cong {len(docs)} dieu tu cac file PDF.")
    
    # Chia nhỏ các Điều lớn thành các chunk nhỏ hơn và làm giàu ngữ cảnh (Context Enrichment) cho từng chunk
    print("Dang chia nho va lam giau ngu canh cho tung chunk (Context Enrichment)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    
    final_docs = []
    for doc in docs:
        meta = doc.metadata
        context_header = f"[Nguồn: {meta['source_document']} | {meta['chapter']} | {meta['article_title']} {meta['article_name']}]\n"
        chunks = text_splitter.split_text(doc.page_content)
        for chunk in chunks:
            enriched_content = context_header + "Nội dung luật:\n" + chunk
            final_docs.append(Document(
                page_content=enriched_content,
                metadata=meta
            ))
            
    print(f"Tong so chunks sau khi lam giau ngu canh: {len(final_docs)}")
    
    vectorstore = Chroma.from_documents(documents=final_docs, embedding=embeddings, persist_directory=db_path)
    return vectorstore.as_retriever(search_kwargs={"k": 15})

retriever = setup_vector_db()

# --- 2. SETUP RERANKER ---
from sentence_transformers import CrossEncoder
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"---Using device for Reranker: {device}---")
reranker = CrossEncoder("BAAI/bge-reranker-base", device=device)
