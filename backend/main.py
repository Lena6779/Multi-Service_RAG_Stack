from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import requests

from config import settings

app = FastAPI(title="RAG API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
collection = client.get_or_create_collection(
    settings.COLLECTION_NAME, configuration={"hnsw": {"space": "cosine"}}
)


@app.get("/health")
def health():
    ollama_ok = False
    try:
        r = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except requests.RequestException:
        pass
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_ok else "unavailable",
        "ollama_url": settings.OLLAMA_URL,
        "documents": collection.count(),
    }


@app.get("/")
def root():
    return {"message": "RAG API running in Docker", "model": settings.MODEL_NAME}


class Document(BaseModel):
    text: str


@app.post("/documents")
def add_document(doc: Document):
    doc_id = f"doc_{collection.count() + 1}"
    collection.add(documents=[doc.text], ids=[doc_id])
    return {"added": doc_id, "documents": collection.count()}


class Question(BaseModel):
    question: str


@app.post("/ask")
def ask(q: Question):
    if collection.count() == 0:
        return {"answer": "No documents yet. Add some with POST /documents.", "sources": []}

    results = collection.query(
        query_texts=[q.question],
        n_results=min(settings.MAX_RESULTS, collection.count()),
    )

    # Keep only close-enough matches (cosine distance: 0 = identical, 2 = opposite)
    docs = []
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        if settings.DEBUG:
            print(f"[ask] distance={dist:.3f} doc={doc[:60]!r}")
        if dist <= settings.CONFIDENCE_THRESHOLD:
            docs.append(doc)

    if not docs:
        return {"answer": "I don't have information about that in my documents.", "sources": []}

    context = "\n\n".join(docs)
    response = requests.post(
        f"{settings.OLLAMA_URL}/api/chat",
        json={
            "model": settings.MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Answer using ONLY the context provided. "
                 "If the answer isn't in the context, say you don't know."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {q.question}"},
            ],
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    return {"answer": response.json()["message"]["content"], "sources": docs}