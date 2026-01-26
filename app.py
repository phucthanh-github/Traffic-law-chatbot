import chainlit as cl
from graph import app_graph # Import graph từ file graph.py

@cl.on_chat_start
async def start():
    """Hàm chạy khi người dùng bắt đầu phiên chat mới"""
    cl.user_session.set("graph", app_graph)
    await cl.Message(content="Chào bạn! Tôi là trợ lý AI. Hãy hỏi tôi bất cứ điều gì!").send()

@cl.on_message
async def main(message: cl.Message):
    """Hàm chạy mỗi khi người dùng gửi tin nhắn"""
    graph = cl.user_session.get("graph")
    
    # Gọi Graph chạy (LangGraph)
    inputs = {"question": message.content}
    
    # Gửi tin nhắn chờ
    msg = cl.Message(content="")
    await msg.send()
    
    # Streaming kết quả từng bước
    # Lưu ý: LangGraph stream trả về từng node output
    final_answer = ""
    
    # Hiển thị quá trình suy nghĩ (Thinking Process)
    async with cl.Step(name="Self-RAG Agent") as root_step:
        root_step.input = message.content
        
        # Chuyển đổi hàm stream synchronous sang async (giả lập để demo đơn giản)
        # Trong thực tế nên dùng astream, nhưng Groq/LangGraph đôi khi conflict async
        for output in graph.stream(inputs):
            for key, value in output.items():
                # Tạo Step con cho từng Node (Retrieve, Check, Generate...)
                async with cl.Step(name=f"Node: {key}") as step:
                    step.input = value.get("question", "") or "Processing..."
                    
                    if "documents" in value:
                        step.output = f"Tìm thấy {len(value['documents'])} tài liệu."
                    if "generation" in value:
                        step.output = value["generation"]
                        final_answer = value["generation"]
                    else:
                        step.output = "Done."

    # Gửi câu trả lời cuối cùng
    msg.content = final_answer
    await msg.update()