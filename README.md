# Multi-Service_RAG_Stack

A multi-service RAG API built with Docker Compose.

A FastAPI backend and an Ollama LLM server running as two containers with Docker Compose. The backend stores documents in ChromaDB, and both the database and the downloaded models are kept in named volumes so the data survives container restarts. All settings are loaded from environment variables, so behavior can be changed without editing code.

## Project structure

```
Multi-Service_RAG_Stack/
├── docker-compose.yml
├── README.md
├── .env              # settings and secrets (not committed)
├── .env.example      # template for .env, no secrets
├── .gitignore
└── backend/
    ├── Dockerfile
    ├── .dockerignore
    ├── config.py     # loads settings from environment variables
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
- Settings are passed to the backend from the `.env` file with `env_file: .env`. See [Configuration](#configuration).

## Volumes

| Volume | Mounted at | Stores |
|---|---|---|
| `chroma_data` | `/app/chroma_data` (backend) | ChromaDB documents and embeddings |
| `ollama_data` | `/root/.ollama` (ollama) | Downloaded Ollama models |

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), running
- If Ollama is installed on your computer, quit it first so port `11434` is free

## Configuration

All settings live in `backend/config.py`, which reads them from environment variables and falls back to sensible defaults. Docker Compose loads the values from a `.env` file in the project root (`env_file: .env`).

- `.env` holds the real values, including secrets. It is listed in `.gitignore` and `backend/.dockerignore`, so it is never committed or copied into the image.
- `.env.example` documents every setting with no secrets and is committed to Git.

| Variable | Value in `.env` | Default in `config.py` | Purpose |
|---|---|---|---|
| `OLLAMA_URL` | `http://ollama:11434` | `http://localhost:11434` | Where the backend reaches Ollama |
| `MODEL_NAME` | `llama3.2:1b` | `llama3.2:1b` | Ollama model used for answers |
| `CHROMA_PATH` | `/app/chroma_data` | `./chroma_data` | ChromaDB storage path |
| `COLLECTION_NAME` | `documents` | `documents` | ChromaDB collection name |
| `MAX_RESULTS` | `5` | `3` | Number of documents retrieved per question |
| `CONFIDENCE_THRESHOLD` | `1.0` | `1.2` | Max cosine distance to count as a match (0 = identical, 2 = opposite) |
| `DEBUG` | `true` | `false` | Prints the config and match distances to the logs |
| `DOCS_DIRECTORY` | `/app/docs` | `./docs` | Folder for source documents |
| `OPENAI_API_KEY` | *(your key)* | *(empty)* | Reserved for an OpenAI fallback |

With `DEBUG=true`, the backend prints its configuration on startup:

```
backend-1  | === Configuration ===
backend-1  |   Ollama URL: http://ollama:11434
backend-1  |   Model: llama3.2:1b
backend-1  |   ChromaDB: /app/chroma_data
backend-1  |   Max Results: 5
backend-1  |   Threshold: 1.0
```

To change a setting, edit `.env` and run `docker compose up` again. (`docker compose restart` does not reload `.env`.)

### Verifying the configuration

1. In `.env`, change `MODEL_NAME=llama3.2:1b` to `MODEL_NAME=llama3.2:3b`.
2. Run `docker compose up`.
3. The startup printout shows `Model: llama3.2:3b`, and `GET /` returns `"model": "llama3.2:3b"`.
4. Change it back to `llama3.2:1b` and run `docker compose up` again.

## Getting started

1. Clone the repo and move into the project folder:

   ```bash
   git clone https://github.com/Lena6779/Multi-Service_RAG_Stack.git
   cd Multi-Service_RAG_Stack
   ```

2. Create your `.env` from the template, then add any secrets:

   ```bash
   cp .env.example .env
   ```

   On Windows Command Prompt, use `copy .env.example .env`.

3. Build and start both containers:

   ```bash
   docker compose up --build
   ```

   The first build takes several minutes. Wait for:

   ```
   backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

4. In a second terminal, download the model into the Ollama container (only needed once):

   ```bash
   docker compose exec ollama ollama pull llama3.2:1b
   ```

5. Open `http://localhost:8000/health` to confirm everything is connected.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Confirms the API is running and shows the model name |
| `GET` | `/health` | Shows Ollama connection status and document count |
| `POST` | `/documents` | Adds a document to ChromaDB |
| `POST` | `/ask` | Answers a question using the closest matching documents |

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

`POST /ask` with body:

```json
{"question": "What does Docker Compose do?"}
```

Response (answer wording varies):

```json
{"answer": "Docker Compose runs multiple containers together.", "sources": ["Docker Compose runs multiple containers together."]}
```

If no document is within `CONFIDENCE_THRESHOLD`, the API answers that it doesn't have that information instead of guessing.

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
| `docker compose up` | Start without rebuilding (enough after changing `.env`) |
| `docker compose down` | Stop and remove containers (volumes are kept) |
| `docker compose ps` | Show running containers |
| `docker compose logs backend` | Show backend logs |

## Tech stack

- Python 3.11
- FastAPI and Uvicorn
- ChromaDB
- Ollama (`llama3.2:1b`)
- Docker and Docker Compose
