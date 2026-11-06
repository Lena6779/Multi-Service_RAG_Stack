# Multi-Service_RAG_Stack

A multi-service RAG API built with Docker Compose.

A FastAPI backend and an Ollama LLM server running as two containers with Docker Compose. The backend stores documents in ChromaDB, and both the database and the downloaded models are kept in named volumes so the data survives container restarts.

## Project structure

```
Multi-Service_RAG_Stack/
├── docker-compose.yml
├── README.md
├── .env
├── .gitignore
└── backend/
    ├── Dockerfile
    ├── main.py
    ├── requirements.txt
    └── docs/
        └── sample.txt
```

## Services

| Service | What it does | Port |
|---|---|---|
| `backend` | FastAPI RAG API, built from `backend/Dockerfile` | `8000` |
| `ollama` | Ollama LLM server, using the `ollama/ollama` image | `11434` |

- The backend reaches Ollama at `http://ollama:11434`. Inside the Compose network, containers find each other by service name, not `localhost`.
- `depends_on` makes the backend start after Ollama.
- Settings are passed to the backend as environment variables:
  - `OLLAMA_URL=http://ollama:11434`
  - `MODEL_NAME=llama3.2:1b`

## Volumes

| Volume | Mounted at | Stores |
|---|---|---|
| `chroma_data` | `/app/chroma_data` (backend) | ChromaDB documents and embeddings |
| `ollama_data` | `/root/.ollama` (ollama) | Downloaded Ollama models |

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), running
- If Ollama is installed on your computer, quit it first so port `11434` is free

## Getting started

1. Clone the repo and move into the project folder:

   ```bash
   git clone https://github.com/Lena6779/Multi-Service_RAG_Stack.git
   cd Multi-Service_RAG_Stack
   ```

2. Build and start both containers:

   ```bash
   docker compose up --build
   ```

   The first build takes several minutes. Wait for:

   ```
   backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

3. In a second terminal, download the model into the Ollama container (only needed once):

   ```bash
   docker compose exec ollama ollama pull llama3.2:1b
   ```

4. Open `http://localhost:8000/health` to confirm everything is connected.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Confirms the API is running and shows the model name |
| `GET` | `/health` | Shows Ollama connection status and document count |
| `POST` | `/documents` | Adds a document to ChromaDB |

Interactive docs are at `http://localhost:8000/docs`.

### Examples

`GET /`

```json
{"message": "RAG API running in Docker", "model": "llama3.2:1b"}
```

`GET /health`

```json
{"status": "healthy", "ollama": "connected", "ollama_url": "http://ollama:11434", "documents": 1}
```

`POST /documents` with body:

```json
{"text": "Docker Compose runs multiple containers together."}
```

Response:

```json
{"added": "doc_1", "documents": 1}
```

## Persistence test

1. Add a document with `POST /documents` and confirm `/health` shows `"documents": 1`.
2. Stop and remove the containers:

   ```bash
   docker compose down
   ```

3. Start them again:

   ```bash
   docker compose up
   ```

4. Check `/health` again. It still shows `"documents": 1`, because the data lives in the `chroma_data` volume, not inside the container.

**Result:** the document count was preserved after `down` and `up`. ✅

> Do not use `docker compose down -v` unless you want to delete the volumes and all saved data.

## Useful commands

| Command | What it does |
|---|---|
| `docker compose up --build` | Rebuild and start (use after changing code) |
| `docker compose up` | Start without rebuilding |
| `docker compose down` | Stop and remove containers (volumes are kept) |
| `docker compose ps` | Show running containers |
| `docker compose logs backend` | Show backend logs |

## Tech stack

- Python 3.11
- FastAPI and Uvicorn
- ChromaDB
- Ollama (`llama3.2:1b`)
- Docker and Docker Compose