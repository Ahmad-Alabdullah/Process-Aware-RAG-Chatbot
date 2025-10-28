from fastapi import APIRouter
from pydantic import BaseModel
from app.services.retrieval import hybrid_search
from app.services.llm import ollama_generate, hyde_rewrite
from app.core.config import settings

router = APIRouter()


class AskBody(BaseModel):
    query: str
    top_k: int = int(settings.TOP_K)
    use_hyde: bool = False
    model: str = settings.OLLAMA_MODEL


@router.post("/ask")
def ask(body: AskBody):
    q = hyde_rewrite(body.query, model=body.model) if body.use_hyde else body.query
    ctx = hybrid_search(q, body.top_k)
    context_text = "\n\n".join(f"- {c['text']}" for c in ctx)
    prompt = f"""Beantworte die Frage basierend auf dem Kontext.

                 Frage: {body.query}

                 Kontext:{context_text}

                 Antwort (deutsch, mit kurzen Belegen wenn möglich):

              """
    answer = ollama_generate(prompt, model=body.model)
    return {"answer": answer, "context": ctx}
