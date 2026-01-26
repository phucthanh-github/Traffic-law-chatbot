# SEFT-RAG: Self-Reflective Retrieval-Augmented Generation

SEFT-RAG là một ứng dụng AI tiên tiến kết hợp **Retrieval-Augmented Generation (RAG)** với **Self-Reflective** capabilities. Hệ thống tự động đánh giá độ liên quan của tài liệu được truy xuất và quyết định có cần tìm kiếm trên Internet hay không, trước khi sinh ra câu trả lời.

## 🎯 Tính Năng Chính

- **RAG thông minh**: Kết hợp tri thức từ vector database (Chroma) và Internet (Tavily Search)
- **Self-Reflective Pipeline**: Tự động đánh giá chất lượng tài liệu trước khi sinh câu trả lời
- **Chưng cất kiến thức**: Hỗ trợ Wikipedia + Custom vector embeddings
- **Giao diện người dùng**: Web app hiện đại với Nest.js và Next.js
- **API RESTful**: Backend FastAPI để tích hợp với các ứng dụng khác
- **Backend NestJS**: Một lựa chọn thay thế hoặc bổ sung cho API

## 🏗️ Kiến Trúc Dự Án

```
SEFT-RAG/
├── api.py                 # FastAPI backend với các endpoint chat
├── app.py                 # Chainlit frontend để chat trực tiếp
├── graph.py              # Lõi của hệ thống: LangGraph workflow
├── requirements.txt      # Dependencies Python
├── chroma_db/            # Vector database (Chroma) lưu trữ tài liệu
├── backend/              # NestJS backend (tuỳ chọn)
│   ├── src/
│   ├── test/
│   └── package.json
├── frontend/             # Next.js frontend
│   ├── app/
│   ├── public/
│   └── package.json
└── __pycache__/         # Cache Python
```

## 🚀 Bắt Đầu Nhanh

### Yêu Cầu Hệ Thống
- Python 3.10+
- Node.js 18+
- npm hoặc yarn

### Cài Đặt

#### 1. Clone và Chuẩn Bị Môi Trường Python

```bash
cd d:\SEFT-RAG
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# Hoặc: source venv/bin/activate  # Linux/Mac
```

#### 2. Cài Đặt Dependencies Python

```bash
pip install -r requirements.txt
```

#### 3. Cấu Hình Biến Môi Trường

Tạo file `.env` ở thư mục gốc:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here (tuỳ chọn)
```

Lấy API keys:
- **Groq**: https://console.groq.com/keys
- **Tavily**: https://tavily.com/
- **OpenAI** (tuỳ chọn): https://platform.openai.com/api-keys

#### 4. Khởi Tạo Vector Database (Nếu Cần)

Vector database sẽ tự động tạo nếu không tồn tại. Lần đầu, hệ thống sẽ load dữ liệu từ Wikipedia về Diabetes mellitus.

### Chạy Ứng Dụng

#### Option 1: Chatbot Web (Chainlit)

```bash
chainlit run app.py
```

Truy cập tại: `http://localhost:8000`

#### Option 2: API FastAPI

```bash
python api.py
```

API chạy tại: `http://localhost:8000`

**Endpoint chính:**
- `POST /chat` - Gửi câu hỏi và nhận câu trả lời

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Bệnh tiểu đường là gì?"}'
```

#### Option 3: Backend NestJS (Tuỳ Chọn)

```bash
cd backend
npm install
npm run start:dev
```

NestJS backend chạy tại: `http://localhost:3000`

#### Option 4: Frontend Next.js

```bash
cd frontend
npm install
npm run dev
```

Frontend chạy tại: `http://localhost:3000`

## 📚 Công Nghệ Sử Dụng

### Backend Python
- **LangChain**: Framework cho các LLM applications
- **LangGraph**: Orchestration workflow và state management
- **FastAPI**: Web framework hiệu năng cao
- **Chainlit**: Giao diện chat tương tác
- **Groq**: Model LLM (Llama 3.1 8B Instant) - nhanh và miễn phí
- **Chroma**: Vector database
- **Sentence Transformers**: Embedding models
- **Tavily**: Web search API
- **Wikipedia Loader**: Tải dữ liệu từ Wikipedia

### Backend Node.js
- **NestJS**: Framework TypeScript cho backend
- **Axios**: HTTP client

### Frontend
- **Next.js**: React framework với SSR
- **React 19**: Thư viện UI
- **Tailwind CSS**: Styling

## 🔄 Luồng RAG

```
Câu Hỏi Người Dùng
       ↓
   [RETRIEVE] - Truy xuất từ Vector Database
       ↓
  [GRADE DOCUMENTS] - Đánh giá độ liên quan
       ↓
   Liên quan?
       ├─ YES → [GENERATE] → Trả lời từ Local Docs
       └─ NO  → [WEB SEARCH] → Tìm trên Internet → [GENERATE]
       ↓
   Câu Trả Lời Final
```

## 📖 Chi Tiết Các Nodes trong Graph

### 1. **Retrieve Node**
- Tìm kiếm tài liệu từ Chroma vector database
- Sử dụng embedding từ Sentence Transformers
- Mặc định lấy 4 tài liệu liên quan nhất

### 2. **Grade Documents Node**
- Dùng LLM để đánh giá xem tài liệu có trả lời câu hỏi không
- Trả về JSON với `reasoning` (giải thích) và `binary_score` (yes/no)
- Nếu không liên quan → chuyển sang Web Search

### 3. **Web Search Node**
- Sử dụng Tavily API để tìm kiếm trên Internet
- Trả về 3 kết quả search tốt nhất
- Chỉ kích hoạt khi tài liệu local không đủ

### 4. **Generate Node**
- Sử dụng Groq LLM để sinh câu trả lời
- Input: Câu hỏi + tài liệu (từ Local DB hoặc Web Search)
- Output: Câu trả lời chi tiết

## 📝 Các File Chính

### `graph.py`
Lõi của hệ thống RAG. Định nghĩa:
- Vector database setup
- Các nodes của workflow (retrieve, grade, web_search, generate)
- State management của LangGraph
- Router logic để quyết định next node

### `api.py`
FastAPI server với endpoint `/chat`:
- Nhận câu hỏi từ client
- Chạy graph workflow
- Trả về câu trả lời + các bước thực hiện

### `app.py`
Chainlit chatbot interface:
- Giao diện chat thân thiện
- Hiển thị quá trình suy luận (thinking process)
- Step-by-step visualization của workflow

## ⚙️ Cấu Hình Tùy Chọn

### Thay đổi Model LLM

Trong `graph.py`, tìm dòng:
```python
llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant")
```

**Các options:**
- `mixtral-8x7b-32768` - Mô hình lớn hơn, chất lượng cao hơn
- Hoặc sử dụng OpenAI: `ChatOpenAI(model="gpt-4-turbo")`

### Thay đổi Vector Database Source

Sửa trong `setup_vector_db()`:
```python
loader = WikipediaLoader(query="Your Topic Here", load_max_docs=5)
```

### Điều Chỉnh Chunk Size

Trong `graph.py`:
```python
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
```
- Tăng `chunk_size` → các tài liệu dài hơn
- Tăng `chunk_overlap` → overlap nhiều hơn giữa các chunks

## 📊 Ví Dụ Sử Dụng

### Curl Request

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Điều trị tiểu đường loại 2 như thế nào?"}'
```

### Response Example

```json
{
  "answer": "Điều trị tiểu đường loại 2 bao gồm: ...",
  "steps": [
    {
      "node": "retrieve",
      "content": "Tìm thấy 4 tài liệu."
    },
    {
      "node": "grade_documents",
      "content": "Tài liệu liên quan."
    },
    {
      "node": "generate",
      "content": "Đã sinh câu trả lời."
    }
  ]
}
```

## 🧪 Testing

### Run Unit Tests (Backend NestJS)

```bash
cd backend
npm test
```

### Run E2E Tests

```bash
npm run test:e2e
```

## 🐛 Troubleshooting

### Lỗi: "GROQ_API_KEY not found"
- Kiểm tra file `.env` có tồn tại và có `GROQ_API_KEY`
- Chạy `python -m dotenv`

### Lỗi: "Chroma database connection failed"
- Xóa folder `chroma_db` và chạy lại
- Hệ thống sẽ tự động tạo database mới

### Chainlit UI không hiển thị
- Đảm bảo port 8000 không bị chiếm dụng
- Thử: `chainlit run app.py --port 8080`

### Vector database quá chậm
- Giảm `load_max_docs` trong `setup_vector_db()`
- Sử dụng embedding model nhẹ hơn


