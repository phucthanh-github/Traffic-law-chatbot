import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(dotenv_path=r"d:\SEFT-RAG\.env")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from retriever import retriever, reranker
from huggingface_hub import InferenceClient
from fastapi.responses import StreamingResponse
import asyncio
import json
import uvicorn

app = FastAPI()

class ChatRequest(BaseModel):
    question: str
    chat_history: list = []

client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

def condense_question(question: str, chat_history: list) -> str:
    try:
        history_str = "Không có lịch sử trò chuyện trước đó."
        if chat_history:
            history_parts = []
            for msg in chat_history[-4:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_str = "\n".join(history_parts)
            
        system_prompt = """Bạn là trợ lý tối ưu hóa câu hỏi tra cứu luật giao thông đường bộ Việt Nam. 
Nhiệm vụ của bạn là dựa vào lịch sử trò chuyện (nếu có) và câu hỏi mới của người dùng để viết lại thành một câu hỏi độc lập (standalone question) bằng tiếng Việt để phục vụ tra cứu thông tin trong văn bản pháp luật.

ĐẶC BIỆT: Hãy chuẩn hóa các từ ngữ dân dã, thông thường của người dùng sang thuật ngữ pháp lý chính thức được dùng trong tài liệu luật:
- "xe máy" (dân dã) -> "xe mô tô hoặc xe gắn máy" (Lưu ý: TRÁNH nhầm với "xe máy chuyên dùng" như máy xúc, xe lu, máy kéo)
- "xe con", "xe du lịch", "xe ca" -> "xe ô tô"
- "xe bốn bánh", "xe điện du lịch" -> "xe chở người bốn bánh có gắn động cơ hoặc xe chở hàng bốn bánh có gắn động cơ"
- "vượt đèn đỏ", "vượt đèn vàng", "đi đèn đỏ" -> "không chấp hành hiệu lệnh của đèn tín hiệu giao thông"
- "đi ngược chiều", "chạy ngược chiều" -> "đi ngược chiều của đường một chiều hoặc đi ngược chiều trên đường có biển Cấm đi ngược chiều"
- "nồng độ cồn", "say rượu", "uống rượu bia" -> "điều khiển xe trên đường mà trong máu hoặc hơi thở có nồng độ cồn"
- "lạng lách", "đánh võng" -> "điều khiển xe lạng lách, đánh võng"
- "không đội mũ bảo hiểm" -> "không đội mũ bảo hiểm cho người đi mô tô, xe máy hoặc đội mũ bảo hiểm không cài quai đúng quy cách"
- "chạy quá tốc độ", "bắn tốc độ" -> "điều khiển xe chạy quá tốc độ quy định"
- "đi vào đường cấm", "đường ngược chiều" -> "đi vào đường có biển báo hiệu có nội dung cấm đi vào đối với loại phương tiện đang điều khiển"

YÊU CẦU: Chỉ trả về duy nhất nội dung câu hỏi độc lập đã được chuẩn hóa thuật ngữ pháp lý, không thêm lời dẫn, không giải thích gì thêm."""

        user_content = f"""Lịch sử trò chuyện:
{history_str}

Câu hỏi mới của người dùng: {question}

Câu hỏi độc lập đã chuẩn hóa:"""

        response = client.chat_completion(
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=150,
            temperature=0.1,
        )
        condensed = response.choices[0].message.content.strip()
        print(f"\n[Condense & Translate Query] Original: '{question}' -> Standalone: '{condensed}'")
        return condensed if condensed else question
    except Exception as e:
        print(f"Lỗi condense_question: {e}")
        return question

@app.post("/chat")
async def chat(request: ChatRequest):
    async def event_generator():
        try:
            question = request.question
            chat_history = request.chat_history or []
            
            # Viết lại câu hỏi nếu có lịch sử chat để tăng hiệu quả RAG
            search_query = condense_question(question, chat_history)
            
            # 1. Thực hiện retrieve từ Chroma (CPU/GPU)
            print(f"\n--- RETRIEVE (LOCAL) for: '{search_query}' ---")
            raw_docs = retriever.invoke(search_query)
            print(f"Da tim thay {len(raw_docs)} tai lieu tho.")
            
            # 2. Thực hiện Rerank bằng BAAI/bge-reranker-base
            if raw_docs:
                if reranker is not None:
                    print("--- RERANKING WITH CROSS-ENCODER ---")
                    pairs = [[search_query, doc.page_content] for doc in raw_docs]
                    scores = reranker.predict(pairs)
                    doc_scores = sorted(zip(raw_docs, scores), key=lambda x: x[1], reverse=True)
                    for doc, score in doc_scores:
                        doc.metadata["rerank_score"] = float(score)
                    top_docs = [doc for doc, score in doc_scores[:2]]
                    
                    # In ra console (chỉ sử dụng ASCII để tránh lỗi cp1252 trên Windows)
                    for idx, (doc, score) in enumerate(doc_scores[:2]):
                        title = doc.metadata.get("article_title", "")
                        name = doc.metadata.get("article_name", "")
                        print(f"Top {idx+1}: {title} {name} | Rerank Score: {score:.4f}")
                else:
                    print("--- BYPASSING RERANKER (LOW RAM MODE) ---")
                    top_docs = raw_docs[:2]
                    for idx, doc in enumerate(top_docs):
                        title = doc.metadata.get("article_title", "")
                        name = doc.metadata.get("article_name", "")
                        print(f"Top {idx+1}: {title} {name} (No Rerank Score)")
            else:
                print("Khong tim thay tai lieu tho nao.")
                top_docs = []
                
            print("--- GENERATING ANSWER ---")
            
            # 3. Xây dựng prompt kèm ngữ cảnh và lịch sử cuộc trò chuyện
            context_parts = []
            for doc in top_docs:
                meta = doc.metadata
                source_info = ""
                if "source_document" in meta:
                    source_info += f"[{meta['source_document']}"
                    if "chapter" in meta:
                        source_info += f", {meta['chapter']}"
                    if "article_title" in meta:
                        source_info += f", {meta['article_title']}"
                    if "article_name" in meta:
                        source_info += f" ({meta['article_name']})"
                    source_info += "]"
                else:
                    source_info += "[Tài liệu tham khảo]"
                
                score_val = meta.get("rerank_score")
                score_info = f" | Rerank Score: {score_val:.4f}" if score_val is not None else ""
                context_parts.append(f"Nguồn: {source_info}{score_info}\nNội dung: {doc.page_content}")
            
            context_str = "\n\n".join(context_parts)
            
            system_prompt = f"""Bạn là trợ lý AI chuyên nghiệp về Luật Giao thông đường bộ Việt Nam. 
Nhiệm vụ của bạn là trả lời câu hỏi của người dùng một cách chính xác, rõ ràng và mạch lạc dựa trên ngữ cảnh được cung cấp bên dưới.

Yêu cầu khi trả lời:
1. Chỉ sử dụng thông tin từ ngữ cảnh để trả lời. Không tự bịa đặt thông tin.
2. Trích dẫn rõ ràng cơ sở pháp lý (ví dụ: tên Điều, tên Chương, tên Luật như Luật Đường bộ số 35/2024/QH15 hoặc Nghị định số 168/2024/NĐ-CP) từ phần "Nguồn:" của tài liệu tham khảo.
3. Nếu không tìm thấy câu trả lời trong ngữ cảnh hoặc thông tin không đủ, hãy trả lời trung thực là bạn không có đủ thông tin dựa trên cơ sở pháp lý được cung cấp và đề xuất người dùng hỏi chi tiết hơn hoặc tra cứu thêm.
4. Trình bày câu trả lời đẹp mắt, phân cấp rõ ràng (sử dụng bullet points nếu cần).

Ngữ cảnh tài liệu:
{context_str}"""

            messages = [{"role": "system", "content": system_prompt}]
            
            # Thêm tối đa 4 tin nhắn gần nhất từ lịch sử chat để tránh tràn token
            for msg in chat_history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
            messages.append({"role": "user", "content": question})
            
            # 4. Stream trực tiếp từng token từ Llama 70B của Hugging Face
            for message in client.chat_completion(
                model="meta-llama/Llama-3.3-70B-Instruct",
                messages=messages,
                max_tokens=1024,
                stream=True,
            ):
                token = message.choices[0].delta.content
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            # Báo hiệu kết thúc
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            error_info = {
                "type": "error",
                "content": str(e)
            }
            yield f"data: {json.dumps(error_info)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)