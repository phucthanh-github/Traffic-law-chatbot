# Traffic Law Chatbot

Traffic Law Chatbot is an AI-powered application designed to query and answer questions about **Vietnamese Road Traffic Laws** using **Retrieval-Augmented Generation (RAG)** technology. The system automatically retrieves and ranks relevant information from official legal documents before generating detailed and accurate responses for users.

## 🎯 Key Features

- **Accurate Retrieval (RAG)**: Search for relevant laws in the Chroma vector database built from official Vietnamese legal documents.
- **Optimized Reranking**: Utilize `bge-reranker-base` to score and filter the most relevant document passages for the user's question.
- **Smart Response Generation**: Powered by the `Llama-3.3-70B-Instruct` large language model, fine-tuned on Vietnamese traffic law datasets using **QLoRA (Quantized Low-Rank Adaptation)** to achieve deep domain understanding and precise legal phrasing. Served via Hugging Face Hub API.
- **Modern Interface**: Smooth real-time chat experience (streaming responses) provided by a complete web application built with a NestJS backend and Next.js frontend.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation and Running

#### 1. Prepare Python Environment & Start the AI Service

```bash
cd d:\SEFT-RAG
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```env
HF_TOKEN=your_huggingface_api_key_here
```

Start the FastAPI AI Service:
```bash
python api.py
```
The service will run at `http://localhost:8000`. On the first startup, if the `chroma_db_pdf_v4` database does not exist, the system will automatically parse the PDF files in the root folder and initialize the vector database.

#### 2. Start the Backend (NestJS)

```bash
cd d:\SEFT-RAG\backend
npm install
npm run start:dev
```
The backend gateway will run at `http://localhost:4000`.

#### 3. Start the Frontend (Next.js)

```bash
cd d:\SEFT-RAG\frontend
npm install
npm run dev
```
The user interface will run at `http://localhost:3000`.

## 📚 Tech Stack

### AI Service (Python)
- **FastAPI**: Provides high-performance, real-time chat streaming endpoints.
- **LangChain**: Used for parsing PDF files, splitting text into chunks, and managing the vector database.
- **Chroma**: A local vector database for storing and querying embeddings.
- **Sentence Transformers**: `paraphrase-multilingual-MiniLM-L12-v2` for generating high-quality Vietnamese text embeddings.
- **CrossEncoder**: `bge-reranker-base` to perform document reranking and relevancy ranking.
- **Hugging Face Hub API**: Connects to and streams tokens from the fine-tuned model.
- **QLoRA (Quantized Low-Rank Adaptation)**: Used to fine-tune the foundation model on domestic traffic legal records and case files for specialized Vietnamese law comprehension.

### Backend Gateway (Node.js)
- **NestJS**: Manages API gateway routing and forwards data streams from the FastAPI AI service to the Next.js frontend.

### Frontend (Next.js)
- **Next.js & React**: Powers the interactive web chat interface, rendering streamed responses in real time using Server-Sent Events (SSE).
- **Tailwind CSS**: Modern UI layout with premium dark mode styling.

## 🔄 RAG Workflow

1. **Question Input**: The user sends a question from the Next.js frontend.
2. **Keyword Optimization (Condense)**: FastAPI receives the question, reviews the chat history, and uses Llama-3 to rewrite it into a standalone question using formal Vietnamese legal terms.
3. **Retrieval**: Queries the top 15 most similar document chunks from Chroma using the condensed question.
4. **Reranking**: Uses CrossEncoder to score the 15 retrieved documents and filters for the top 2 best results.
5. **Answer Generation**: Constructs a prompt containing the selected documents along with their legal sources and calls the QLoRA fine-tuned model via Hugging Face API to stream the final answer back to the user.
