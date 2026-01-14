# Conversational RAG: Chat History Context

Dieses Dokument beschreibt die Implementierung von Chat-History-Kontext für Follow-up Fragen.

## Übersicht

Das System ermöglicht kontextuelle Follow-up Fragen durch Einbeziehung der letzten Konversations-Turns.

```
User: "Was ist Elternzeit?"
Assistant: "Elternzeit ist..."
User: "Wie lange dauert sie?"  ← Follow-up mit Pronomen-Referenz
Assistant: (versteht Kontext aus vorheriger Nachricht)
```

## Architektur: Sliding Window

| Parameter | Wert | Begründung |
|-----------|------|------------|
| Window Size | 3 Turns (6 Messages) | Balance zwischen Kontext und Token-Budget |
| Truncation | 200 chars/message | Verhindert Token-Overflow |
| Position | Nach System-Prompt, vor Dokumenten | "Lost in the Middle" Optimierung |

### Token-Budget (8192 Context)

```
┌─────────────────────────────────┐
│ System Prompt         (~200)    │
│ Chat History          (~600)    │
│ Retrieved Documents   (~2000)   │
│ Gating Hint           (~100)    │
│ User Query            (~50)     │
├─────────────────────────────────┤
│ Total Input           ~2950     │
│ Reserved for Output   ~2048     │
│ Buffer                ~3194     │
└─────────────────────────────────┘
```

## Wissenschaftliche Basis

### 1. Sliding Window Memory (2025)

> "Sliding-Window and Hybrid Attention Schemes allow models to maintain a focus on recent information while still having some awareness of older, relevant parts of the conversation."
> — NVIDIA Research, 2025

**Vorteile:**
- Konstante Latenz (O(1) Memory)
- Keine komplexe Zusammenfassung nötig
- Effizient für Short-Term Context

### 2. History-Aware Retrieval

> "To handle follow-up questions effectively, RAG systems are implementing 'history-aware' retrieval. This involves rewriting vague or context-dependent questions into clear, standalone queries."
> — TowardsAI, 2025

**Unser Ansatz:**
- Phase 1: Direkte History-Injection (implementiert)
- Phase 2: Query Reformulation (optional, zukünftig)

### 3. Context Position Optimization

> "The synergy between long context windows and RAG is leading to 'retrieval-first, long-context containment,' where RAG systems use long context windows to hold more complete retrieved chunks."
> — RAGFlow, 2025

**Prompt-Struktur (optimiert nach "Lost in the Middle"):**
1. System-Instruktion (oben - höchste Aufmerksamkeit)
2. Chat-History (früh - für Kontext-Verständnis)
3. Dokumente (Mitte)
4. User-Query (unten - höchste Aufmerksamkeit)

### 4. Context Compression (Alternative)

> "Condensing prior exchanges into semantically rich representations helps prevent excessive data from diluting retrieval quality."
> — Medium, 2025

**Nicht implementiert, da:**
- 3 Turns (~600 Tokens) sind klein genug
- Compression würde Latenz erhöhen
- Truncation auf 200 chars/msg ist ausreichend

## Implementierung

### Backend

1. `AskBody` erhält `chat_history: List[ChatMessage]`
2. `_format_chat_history()` formatiert History für Prompt
3. Max 3 Turns, truncated auf 200 chars

### Frontend

1. `askQuestionStream()` erhält `chat_history` Parameter
2. Letzte 6 Messages werden mitgesendet

## Referenzen

1. **Sliding Window Attention**: Raschka, S. "Efficient Attention Schemes for LLMs" (2024)
2. **Conversational RAG**: TowardsAI "History-Aware RAG Systems" (2025)
3. **Context Engineering**: RAGFlow "Context Optimization Strategies" (2025)
4. **Lost in the Middle**: Liu et al. "Position Bias in Long Contexts" (2023)
5. **Memory Management**: IJSRM "LLM Conversation Memory Strategies" (2025)

## Dateien

- `server/app/core/models/askModel.py` - `ChatMessage` und `chat_history` Feld
- `server/app/core/prompt_builder.py` - `_format_chat_history()` Funktion
- `client/lib/api/streaming.ts` - Request mit History
- `client/components/feature/chat/chat-container.tsx` - History mitschicken
