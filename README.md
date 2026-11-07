# Multi-Service_RAG_Stack

A multi-service RAG API built with Docker Compose.

A FastAPI backend and an Ollama LLM server running as two containers with Docker Compose. The backend stores documents in ChromaDB, and both the database and the downloaded models are kept in named volumes so the data survives container restarts. All settings are loaded from environment variables, so behavior can be changed without editing code.

## Project structure

```
Multi-Service_RAG_Stack/
├── docker-compose.yml
├── README.md
├── .env              # secrets only (not committed)
├── .env.example      # template for .env
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
- Settings are passed to the backend as environment variables in `docker-compose.yml`, and secrets come from `.env`. See [Configuration](#configuration).

## Volumes

| Volume | Mounted at | Stores |
|---|---|---|
| `chroma_data` | `/app/chroma_data` (backend) | ChromaDB documents and embeddings |
| `ollama_data` | `/root/.ollama` (ollama) | Downloaded Ollama models |

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), running
- If Ollama is installed on your computer, quit it first so port `11434` is free

## Configuration

All settings live in `backend/config.py`, which reads them from environment variables and falls back to defaults. Plain settings are set in `docker-compose.yml` under `environment:`. Secrets (only `OPENAI_API_KEY`) go in a `.env` file in the project root, which is listed in `.gitignore` and never committed.

| Variable | Value in Compose | Default in `config.py` | Purpose |
|---|---|---|---|
| `OLLAMA_URL` | `http://ollama:11434` | `http://localhost:11434` | Where the backend reaches Ollama |
| `MODEL_NAME` | `llama3.2:1b` | `llama3.2:1b` | Ollama model used for answers |
| `CHROMA_PATH` | `/app/chroma_data` | `./chroma_data` | ChromaDB storage path |
| `COLLECTION_NAME` | `documents` | `documents` | ChromaDB collection name |
| `MAX_RESULTS` | `5` | `3` | Number of documents retrieved per question |
| `CONFIDENCE_THRESHOLD` | `1.0` | `1.2` | Max cosine distance to count as a match (0 = identical, 2 = opposite) |
| `DEBUG` | `true` | `false` | Prints the config and match distances to the logs |
| `DOCS_DIRECTORY` | `/app/docs` | `./docs` | Folder for source documents |
| `OPENAI_API_KEY` | *(set in `.env`)* | *(empty)* | Reserved for an OpenAI fallback |

With `DEBUG=true`, the backend prints its configuration on startup:

```
backend-1  | === Configuration ===
backend-1  |   Ollama URL: http://ollama:11434
backend-1  |   Model: