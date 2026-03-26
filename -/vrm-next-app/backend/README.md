# Backend Setup Instructions

## Prerequisites
- Python 3.8+
- pip

## Installation

1. Navigate to the backend directory:
```bash
cd -/vrm-next-app/backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install flask flask-cors pinecone-client python-dotenv groq sentence-transformers
```

## Running the Backend

The backend server will run on `http://localhost:3000`

```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:3000
```

## API Endpoints

### POST /api/chat
Handles chat messages and returns nutrition advice.

**Request Body:**
```json
{
  "message": "Is protein good for building muscle?"
}
```

**Response:**
```json
{
  "response": "...",
  "answerType": "fact",
  "contextButtons": [...],
  "corrections": [...]
}
```

## Environment Variables

The backend uses the following environment variables from `.env`:
- `PINECONE_API_KEY` - Your Pinecone API key
- `GROQ_API_KEY` - Your Groq API key
- `PINECONE_INDEX_NAME` - Pinecone index name (default: nutrition-myths)
- `PINECONE_ENVIRONMENT` - Pinecone environment

## Troubleshooting

If you get connection errors:
1. Make sure the backend is running on port 3000
2. Check that CORS is enabled
3. Verify your API keys are correct in `.env`
