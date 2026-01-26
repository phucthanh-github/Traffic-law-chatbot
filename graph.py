import os
from dotenv import load_dotenv
from typing import List
from typing_extensions import TypedDict
from langchain_core.documents import Document 
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field 
from langgraph.graph import END, StateGraph
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import JsonOutputParser
load_dotenv()

# --- 1. SETUP TOOLS ---
def setup_vector_db():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    if os.path.exists("./chroma_db"):
        return Chroma(persist_directory="./chroma_db", embedding_function=embeddings).as_retriever()
    # Fallback load nếu chưa có DB
    loader = WikipediaLoader(query="Diabetes mellitus", load_max_docs=1, doc_content_chars_max=10000)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    vectorstore = Chroma.from_documents(documents=splitter.split_documents(docs), embedding=embeddings, persist_directory="./chroma_db")
    return vectorstore.as_retriever()

retriever = setup_vector_db()
llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant")
web_search_tool = TavilySearchResults(k=3)

# --- 2. GRAPH NODES ---
class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[Document]
    web_search: str 

def retrieve(state):
    print("---RETRIEVE (LOCAL)---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question, "web_search": "no"}

def web_search(state):
    print("---WEB SEARCH (INTERNET)---")
    question = state["question"]
    docs = web_search_tool.invoke({"query": question})
    # Chuẩn hóa kết quả Web thành Document object
    web_results = "\n".join([d["content"] for d in docs])
    web_results = [Document(page_content=web_results)]
    # Đánh dấu là đã search web
    return {"documents": web_results, "question": question, "web_search": "yes"}

def generate(state):
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    prompt = ChatPromptTemplate.from_template(
        """Bạn là trợ lý AI. Dựa vào ngữ cảnh để trả lời câu hỏi.
        Ngữ cảnh: {context}
        Câu hỏi: {question}
        Câu trả lời:"""
    )
    chain = prompt | llm
    generation = chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation.content}

def grade_documents(state):
    """
    Trọng tài: Quyết định dùng Local Docs hay phải ra Web Search
    PHIÊN BẢN NÂNG CẤP: Dùng JSON Parser và bắt suy luận (Reasoning)
    """
    print("---CHECK RELEVANCE---")
    question = state["question"]
    documents = state["documents"]
    
    # 1. Định nghĩa cấu trúc đầu ra mong muốn
    class GradeDocuments(BaseModel):
        reasoning: str = Field(description="Giải thích ngắn gọn tại sao liên quan hoặc không")
        binary_score: str = Field(description="'yes' nếu tài liệu chứa câu trả lời, 'no' nếu không")

    parser = JsonOutputParser(pydantic_object=GradeDocuments)

    # 2. Prompt ép kiểu JSON và bắt suy luận
    system_prompt = """Bạn là một giám khảo nghiêm khắc.
    Nhiệm vụ: Đánh giá xem Tài liệu (Document) có chứa thông tin để trả lời Câu hỏi (Question) không.
    
    Quy tắc:
    - Nếu tài liệu nói về chủ đề khác hoàn toàn (ví dụ: Hỏi về Chính trị nhưng tài liệu về Y tế) -> Trả về 'no'.
    - Đừng cố gắng gượng ép. Nếu không chắc chắn -> Trả về 'no'.
    
    Định dạng trả về (JSON):
    {{
        "reasoning": "Giải thích tại sao",
        "binary_score": "yes" hoặc "no"
    }}
    """
    
    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt), 
        ("human", "Document: {document}\nQuestion: {question}")
    ])
    
    # Chain: Prompt -> Model -> JSON Parser
    grader = grade_prompt | llm | parser
    
    filtered_docs = []
    has_relevant_docs = False
    
    for d in documents:
        try:
            score = grader.invoke({"question": question, "document": d.page_content})
            
            # In ra lý do để debug
            print(f"Doc Check: {score['binary_score']} | Lý do: {score['reasoning']}")
            
            if score['binary_score'].lower() == "yes":
                filtered_docs.append(d)
                has_relevant_docs = True
        except Exception as e:
            print(f"Lỗi chấm điểm: {e}")
            # Nếu lỗi, thà bỏ qua còn hơn lấy rác
            continue
            
    # LOGIC QUYẾT ĐỊNH
    if not has_relevant_docs:
        print("---DECISION: LOCAL DOCS POOR -> SWITCH TO WEB SEARCH---")
        # Quan trọng: Trả về documents rỗng để node Generate không bị nhiễu
        return {"documents": [], "question": question, "web_search": "yes"}
    else:
        print("---DECISION: LOCAL DOCS GOOD---")
        return {"documents": filtered_docs, "question": question, "web_search": "no"}
    
def check_hallucinations(state):
   
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    web_search_flag = state.get("web_search", "no")

    class GradeHallucinations(BaseModel):
        binary_score: str = Field(description="'yes' or 'no'")
    class GradeAnswer(BaseModel):
        binary_score: str = Field(description="'yes' or 'no'")

    hallucination_grader = (ChatPromptTemplate.from_messages([
        ("system", "Câu trả lời có dựa trên facts không?"), ("human", "Facts: {documents}\nAnswer: {generation}")
    ]) | llm.with_structured_output(GradeHallucinations))
    
    answer_grader = (ChatPromptTemplate.from_messages([
        ("system", "Câu trả lời có giải quyết câu hỏi không?"), ("human", "Question: {question}\nAnswer: {generation}")
    ]) | llm.with_structured_output(GradeAnswer))

    is_grounded = False
    try:
        score = hallucination_grader.invoke({"documents": documents, "generation": generation})
        is_grounded = score.binary_score.lower() == "yes"
    except: is_grounded = True # Fallback

    if is_grounded:
        print("---DECISION: GROUNDED---")
        is_useful = False
        try:
            score_ans = answer_grader.invoke({"question": question, "generation": generation})
            is_useful = score_ans.binary_score.lower() == "yes"
        except: is_useful = True
        
        if is_useful:
            return "useful"
        else:
            if web_search_flag == "no":
                return "web_search"
            else:
                return "useful" 
    else:
        print("---DECISION: HALLUCINATION (RE-GENERATE)---")
        return "generate"

# --- 3. BUILD GRAPH ---
workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("web_search", web_search)
workflow.add_node("generate", generate)

# Logic luồng đi
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")

def decide_to_generate(state):
    if state["web_search"] == "yes":
        return "web_search"
    return "generate"

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "web_search": "web_search",
        "generate": "generate"
    }
)

workflow.add_edge("web_search", "generate")

def route_after_check(state):
    pass 

workflow.add_conditional_edges(
    "generate",
    check_hallucinations,
    {
        "useful": END,              # Ngon rồi -> Kết thúc
        "generate": "generate",     # Bịa đặt -> Viết lại
        "web_search": "web_search"  # Lạc đề (Local) -> Tìm Google
    }
)

app_graph = workflow.compile()