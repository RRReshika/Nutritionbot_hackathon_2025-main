# Snack Intel — Nutrition Myth-Busting Chatbot

Snack Intel is a lightweight, fast, and practical nutrition assistant designed to clear up common confusion around food. It detects whether a user’s question is based on a myth or a real fact, retrieves verified information from a curated nutrition database, and delivers clear, trustworthy explanations.

The aim is to make nutrition simple, accurate, and accessible without unnecessary noise.

---

## Features

### Myth Detection
Identifies whether a question contains a nutrition myth and responds with the correct evidence-based explanation.

### Data Filtering
Returns only high-quality, relevant chunks from the nutrition knowledge base. Unrelated or low-value content is removed before generating the final answer.

### Modern Chat Interface
Glass-panel styled UI with optional VRM avatar support, designed to feel clean and modern.

### Fast Query Processing
Uses Groq AI for intent analysis and Pinecone for semantic search, resulting in fast and accurate responses.

---

## Architecture Overview

### Frontend (Next.js)
- Glass-style chat UI  
- Optional 3D VRM avatar using Three.js  
- Voice input integration  

### Backend (Node.js / Flask)
- LLM intent analysis  
- Query filtering and metadata extraction  
- Pinecone semantic search  
- Answer construction pipeline  

### Vector Database (Pinecone)
- Stores nutrition facts, myth explanations, and verified evidence chunks.

---

## Project Structure

/frontend
components/
pages/
styles/

/backend
app.py or server.js
llm_client.py
pinecone_client.py
embeddings.py
config.py

/data
nutrition.json


---

## How to Run

### 1. Clone the repository


git clone <repo-url>


### 2. Install dependencies

Frontend:


cd frontend
npm install
npm run dev


Backend (Python):


cd backend
pip install -r requirements.txt
python app.py


### 3. Add environment variables

Create a `.env` file with:


PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=nutrition-index
GROQ_API_KEY=your_key


---

## How It Works

1. User asks a food or nutrition question.  
2. The LLM analyses the intent and detects myth vs fact.  
3. Pinecone retrieves the most relevant verified information.  
4. The backend filters and structures the answer.  
5. The UI displays it cleanly through the chat interface.

---

## Challenges Addressed

- Keeping LLM responses consistent and structured  
- Ensuring only relevant, high-quality data is used  
- Making the UI readable on different screen sizes  
- Balancing performance with visual design  
- Maintaining accuracy and clarity in answers  

---

## Why Snack Intel Works

- Prioritises clarity and factual accuracy  
- Uses fast, efficient tools (Groq + Pinecone)  
- Designed to solve real user confusion around nutrition  
- Simple, modern interface accessible to anyone  

---

## Team

Created by Reshika Raja(rrreshika) and Aishwariya (Aishu11) 
combining design, backend engineering, and data handling to build a clear and reliable nutrition assistant.

