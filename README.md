# SemanticSearchNCO

A hybrid search system for Indian National Classification of Occupations (NCO) data using BM25 and vector semantic search.

## Features

- **Hybrid Search**: Combines BM25 (keyword-based) and vector semantic search
- **Role Discovery**: Search through 3,446+ occupation roles from NCO 2015
- **Fast API Backend**: Built with FastAPI and ChromaDB
- **Modern Frontend**: React-based web interface
- **Relevance Scoring**: Weighted combination of search algorithms

## Tech Stack

### Backend
- **FastAPI** - API framework
- **ChromaDB** - Vector database
- **Sentence Transformers** - Text embeddings
- **Rank BM25** - Keyword search
- **NLTK** - Text processing

### Frontend
- **React** - User interface
- **Vite** - Build tool
- **Axios** - HTTP client

## Quick Start

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.app:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage

1. Enter a job description or role name in the search bar
2. View results ranked by relevance score
3. Each result shows:
   - Role title and number
   - Chunk text from role description
   - BM25, Vector, and Combined scores

## API Endpoints

- `POST /search` - Hybrid search with query text
- `GET /role/{role_number}` - Get specific role description

## Data Source

Based on **National Classification of Occupations (NCO) 2015** published by the Government of India, containing detailed descriptions of occupational roles across various industries and sectors.

## Project Structure

```
├── backend/
│   ├── app/           # FastAPI application
│   ├── data/          # NCO data files
│   └── db/            # Database files
├── frontend/
│   └── src/
│       └── components/ # React components
└── README.md
```

## Prototype screenshots

<img width="1919" height="989" alt="image" src="https://github.com/user-attachments/assets/71118195-8726-409b-b1c2-1c7f17716203" /><br>

<img width="1919" height="980" alt="image" src="https://github.com/user-attachments/assets/daa11d42-e6b0-4216-900f-2d2dcd5767d3" />

---
