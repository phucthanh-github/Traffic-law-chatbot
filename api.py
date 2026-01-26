from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph import app_graph # Import cái graph đã compile từ file graph.py
import uvicorn

app = FastAPI()

class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        inputs = {"question": request.question}
        final_answer = ""
        steps = []

        # Chạy Graph và thu thập từng bước
        for output in app_graph.stream(inputs):
            for key, value in output.items():
                step_info = {
                    "node": key,
                    "content": ""
                }
                if "documents" in value:
                    step_info["content"] = f"Tìm thấy {len(value['documents'])} tài liệu."
                if "web_search" in value and value["web_search"] == "yes":
                     step_info["content"] = "Đang tìm kiếm trên Internet..."
                if "generation" in value:
                    final_answer = value["generation"]
                    step_info["content"] = "Đã sinh câu trả lời."

                steps.append(step_info)

        return {
            "answer": final_answer,
            "steps": steps # Trả về cả quy trình suy nghĩ để hiển thị
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)