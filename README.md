<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/LangChain-1.1-1C3C3C?logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker Compose">
  <img src="https://img.shields.io/badge/Lizenz-MIT-green?logo=opensourceinitiative&logoColor=white" alt="MIT License">
  <img src="https://img.shields.io/github/actions/workflow/status/Ahmad-Alabdullah/Process-Aware-RAG-Chatbot/ci-cd.yml?branch=main&label=CI%2FCD&logo=githubactions&logoColor=white" alt="CI/CD">
</p>

<h1 align="center">🧠 NeuraPath</h1>
<p align="center"><strong>Process-Aware RAG Chatbot für Hochschulverwaltungen</strong></p>
<p align="center"><em>Lokaler, quellengestützter, prozessbewusster Assistent — keine Cloud-APIs, volle Datensouveränität.</em></p>

<p align="center">
  <a href="#erste-schritte">Erste Schritte</a> · <a href="#features">Features</a> · <a href="#reproduzierbarkeit-und-evaluation">Evaluation</a> · <a href="#weiterentwicklung">Ausblick</a>
</p>

---

> Begleit-Repository zur Bachelorarbeit **„Chatbot für eine Hochschulverwaltung: Unterstützung von Mitarbeitenden und Professoren in Hochschulprozessen"** — Hochschule Karlsruhe, WS 2025/26, Note **1,0**.

---

## Inhaltsverzeichnis

<details>
<summary>Aufklappen</summary>

- [Kurzüberblick](#kurzüberblick)
- [Problemstellung und Motivation](#problemstellung-und-motivation)
- [Forschungsfragen und Hypothesen](#forschungsfragen-und-hypothesen)
- [Zentrale Ergebnisse](#zentrale-ergebnisse)
- [Wissenschaftlicher Beitrag](#wissenschaftlicher-beitrag)
- [Systemüberblick](#systemüberblick)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Erste Schritte](#erste-schritte)
- [Nutzung](#nutzung)
- [Reproduzierbarkeit und Evaluation](#reproduzierbarkeit-und-evaluation)
- [Projektstruktur](#projektstruktur)
- [Entwicklung](#entwicklung)
- [Production Deployment](#production-deployment)
- [Limitierungen](#limitierungen)
- [Zitieren](#zitieren)
- [Mitwirken](#mitwirken)
- [Weiterentwicklung](#weiterentwicklung)
- [Lizenz](#lizenz)

</details>

---

## Kurzüberblick

| Aspekt | Beschreibung |
|:---|:---|
| **Domäne** | Hochschulverwaltung — wissensintensive, regelgebundene Prozesse |
| **Kernproblem** | Prozesswissen ist über BPMN-Modelle, Richtlinien, Sonderfall-Dokumente und implizites Erfahrungswissen verteilt |
| **Kernidee** | Kombination aus **Dokumentenevidenz** (RAG) und **Prozessstrukturwissen** (BPMN-Graph + Gating) |
| **Betriebsmodell** | **Local-first / On-Premise** — keine Cloud-LLM-APIs, lokale Modelle via Ollama |
| **Systemrolle** | Assistenzsystem — **kein** WfMS, **keine** rechtsverbindliche Entscheidungsinstanz |
| **Forschungsrahmen** | Design-Science-Artefakt mit Hypothesen H1–H4, Ablationen, Optimierung und Nutzerstudie |

---

## Problemstellung und Motivation

Hochschulverwaltungen bearbeiten eine Vielzahl wiederkehrender, aber ausnahmebehafteter Prozesse — etwa in der Prüfungsorganisation, Lehrverwaltung oder Antragsbearbeitung. Das dafür relevante Wissen liegt selten in einem einzigen konsistenten Artefakt vor:

| Wissensquelle | Charakteristik |
|:---|:---|
| **BPMN-Modelle** | Idealisierter Ablauf — strukturell, aber nicht immer vollständig |
| **Prozessdokumente** | Richtlinien, Dienstvereinbarungen, Sonderfälle — fragmentiert, oft veraltet |
| **Erfahrungswissen** | Informell, personengebunden — geht bei Personalwechseln verloren |

Gerade bei Personalwechseln, Vertretungen oder Einarbeitung neuer Mitarbeitender entstehen dadurch **Wissenslücken**, inkonsistente Entscheidungen und hohe Abhängigkeit von einzelnen Expert:innen.

**NeuraPath** adressiert diese Lücke mit einer zweigeteilten Wissensbasis:

1. **Dokumentenevidenz** — Retrieval-Augmented Generation (RAG) mit Quellenbelegen
2. **Prozessstrukturwissen** — BPMN-Graph als Restriktionsrahmen für prozesskonforme Antworten

Das Ziel ist nicht „ein weiterer Chatbot", sondern ein **prozessbewusstes Assistenzsystem**, das Antworten nachvollziehbar mit Quellen belegt, Rollen- und Prozesskontext berücksichtigt und in sensiblen Organisationskontexten **lokal** betrieben werden kann.

---

## Forschungsfragen und Hypothesen

> **RQ1:** Wie effektiv unterstützt ein prozessbewusster RAG-Chatbot Verwaltungsprozesse bei unvollständigen BPMN-Modellen und informellen Grauzonen?
>
> **RQ2:** Was braucht es für den produktiven Einsatz an einer Hochschule — insbesondere Rollenmodelle, Berechtigungskonzepte und Governance?

| Hypothese | Aussage | Testmethode |
|:---|:---|:---|
| **H1** (Retrieval) | Hybrid-Retrieval (BM25 + Embeddings + RRF) erhöht Evidenz- und Antwortqualität gegenüber Vector-Only und BM25-Only | OFAT-Ablation |
| **H2** (Gating) | BPMN-Whitelist-Gating reduziert falsche/unerlaubte Prozessschritte gegenüber „Gating AUS" | LLM-Judge |
| **H3** (Grauzonen) | Regelbasierte Behandlung von Grauzonen erhöht Konsistenz in unklaren Sonderfällen | LLM-Judge |
| **H4** (UX) | Der Prototyp erreicht akzeptable Nutzbarkeit (**SUS ≥ 70**) | Nutzerstudie |

---

## Zentrale Ergebnisse

| Hypothese | Kernergebnis | Einordnung |
|:---|:---|:---|
| **H1** | Hybrid Retrieval als **robuste Default-Strategie**; Reranking steigert MRR um ca. **3–7 %** | Überwiegend gestützt |
| **H2** | Process-Aware Gating senkt Fehlerrate von **0.417 → 0.383** | Moderater, plausibler Effekt |
| **H3** | Spekulation in **100 %** der Fälle erkannt, angemessene Behandlung bei **0.0** | ⚠️ Wichtigster negativer Befund |
| **H4** | SUS-Mittelwert von **74.3** | Positives Signal (explorativ, *n* = 3) |
| **Optimierung** | Retrieval-nahe Entscheidungen sind der größte Hebel → **Enhanced Baseline** | Chunking & Embeddings > Feintuning |

<details>
<summary><strong>Enhanced Baseline — kompakte Referenzkonfiguration</strong></summary>

| Parameter | Wert |
|:---|:---|
| **LLM** | `qwen2.5:7b-instruct` |
| **top_k** | `5` |
| **Reranking** | `false` (aus Latenzgründen deaktiviert) |
| **Prompt-Stil** | `cot` |
| **Chunking** | `semantic (qwen3-embedding)` |

</details>

---

## Wissenschaftlicher Beitrag

Dieses Repository dokumentiert nicht nur eine Implementierung, sondern ein **evaluierbares Forschungsartefakt** mit vier Beitragsebenen:

| # | Beitrag | Beschreibung |
|:---:|:---|:---|
| 1 | **Architektur** | Kombination aus Hybrid Retrieval und BPMN-basiertem Process-Aware Gating für Verwaltungsprozesse |
| 2 | **Evaluation** | Mehrdimensionale Bewertung entlang von Retrieval, Faithfulness, Prozesskonformität und Usability |
| 3 | **Domäne** | Übertragung zentraler RAG-Prinzipien auf den Hochschulkontext mit explizitem Umgang mit Grauzonen |
| 4 | **Betrieb** | Konzept für lokalen, governance-fähigen Produktivbetrieb an einer Hochschule |

---

## Systemüberblick

Das System folgt dem Prinzip eines **Assistenz-Overlays**: Es führt keine Prozesse aus, sondern unterstützt Mitarbeitende durch Evidenz, Prozesskontext und transparente Begründungen.

### Pipeline

```
User Query → Guardrails → Query Reformulation → Hybrid Retrieval → Reranking
    → Process-Aware Gating → Prompt Assembly → Lokale LLM-Inferenz → Zitierte Antwort
```

### Designprinzipien

| Prinzip | Bedeutung |
|:---|:---|
| 📄 **Evidenz vor Generierung** | Informationen finden und begründen, nicht „erfinden" |
| 🔀 **Prozesskontext als Restriktion** | BPMN dient als Strukturwissen für erlaubte Handlungskorridore |
| 🔒 **Local-first** | Sensible Organisationsdaten verbleiben auf lokaler Infrastruktur |
| 🎯 **Transparenz statt Scheinpräzision** | Quellenbelege und Confidence Badge sind Hilfen, keine Wahrheitsgarantie |
| 🧪 **Ablationsfähigkeit** | Retrieval-Modi, Gating, Prompt-Stile und Modelle sind gezielt vergleichbar |

---

## Features

| Feature | Beschreibung |
|:---|:---|
| 🔍 **Hybrid Retrieval** | BM25 (OpenSearch) + Dense Embeddings (Qdrant) mit Reciprocal Rank Fusion |
| 🔄 **BPMN-Prozessbewusstsein** | Import von BPMN 2.0 als Knowledge Graph (Neo4j) für Kontextsteuerung |
| 🎛️ **Process-Aware Gating** | Drei Modi: Lokale Sicht, Whitelist, Bypass — positions- und rollenabhängig |
| 🛡️ **Query Guardrails** | LLM-basierte Intent-Klassifikation filtert Off-Topic-Anfragen |
| 🧩 **Query Reformulation** | History-Aware Reformulierung löst Anaphern auf und präzisiert Folgefragen |
| 📊 **Cross-Encoder Reranking** | Präzisions-Ranking mittels Cross-Encoder-Modellen |
| 💬 **Streaming-Antworten** | Echtzeit-Token-Streaming über Server-Sent Events (SSE) |
| 📄 **Dokumenten-Ingestion** | PDF-Verarbeitung mit OCR (Tesseract), semantischem Chunking, Multi-Index |
| 🎯 **Confidence Badge** | Heuristische Evidenzstärke-Anzeige als Transparenzsignal |
| 🔒 **Lokale LLM-Inferenz** | On-Premise via Ollama (Qwen, Gemma) — keine Daten verlassen das Netzwerk |
| 🧪 **Evaluations-Framework** | OFAT-Ablationen, GSO-Optimierung, LLM-Judge-Metriken |
| 🚀 **CI/CD & Auto-Updates** | GitHub Actions → GHCR, Watchtower für automatische Container-Updates |

---

## Tech Stack

<table>
<tr><td>

### Backend

| Technologie | Einsatz |
|:---|:---|
| 🐍 Python 3.11 | Kern-Runtime |
| ⚡ FastAPI + Uvicorn | REST API & SSE Streaming |
| 🦜 LangChain / LangGraph | LLM-Orchestrierung |
| 🤖 Ollama | Lokale LLM-Inferenz |
| 🔎 OpenSearch | BM25 Index |
| 📐 Qdrant | Vektor-Datenbank |
| 🕸️ Neo4j | BPMN Knowledge Graph |
| 🐘 PostgreSQL | Metadaten & Evaluation |
| 🔴 Redis | Ingestion Streaming |

</td><td>

### Frontend

| Technologie | Einsatz |
|:---|:---|
| ⚛️ Next.js 16 + React 19 | SSR & App Router |
| 🎨 Tailwind CSS v4 | Styling |
| 🧱 Radix UI | UI Primitives |
| 📦 TanStack Query | Server-State |
| 🔐 NextAuth.js | Auth |
| ✅ Zod + RHF | Validierung |

### Infrastruktur

| Technologie | Einsatz |
|:---|:---|
| 🐳 Docker Compose | Dev & Prod |
| 🌐 Cloudflare Tunnel | Zero Trust |
| 🔄 Watchtower | Auto-Updates |
| ⚙️ GitHub Actions | CI/CD → GHCR |
| 🖥️ NVIDIA GPU | CUDA-Inferenz |

</td></tr>
</table>

---

## Erste Schritte

### Voraussetzungen

| Anforderung | Details |
|:---|:---|
| **Docker Desktop** | ≥ 4.x mit Docker Compose V2 |
| **NVIDIA GPU** | Aktuelle Treiber, min. **12 GB VRAM** empfohlen |
| **Node.js** | ≥ 20 (für Frontend-Entwicklung) |
| **Python** | 3.11 (für Backend-Entwicklung) |
| **Tesseract OCR** | `eng` + `deu` Sprachpakete (im Docker-Image enthalten) |

### Installation

```bash
# 1. Klonen
git clone https://github.com/Ahmad-Alabdullah/Process-Aware-RAG-Chatbot.git
cd Process-Aware-RAG-Chatbot

# 2. Infrastruktur starten (PostgreSQL, OpenSearch, Qdrant, Neo4j, Redis, Ollama)
cd server
docker compose up -d

# 3. LLM-Modelle herunterladen
docker exec -it <ollama-container> ollama pull qwen3:8b
docker exec -it <ollama-container> ollama pull qwen3-embedding:4b

# 4. Backend starten
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 5. Frontend starten (neues Terminal)
cd ../client
npm install && npm run dev
```

> **Konfiguration:** Die `server/.env` ist für lokale Entwicklung vorkonfiguriert. Bei `ENV=local` werden alle Service-URLs automatisch auf `localhost` umgestellt.

<details>
<summary><strong>Wichtige Umgebungsvariablen</strong></summary>

```bash
OLLAMA_MODEL=qwen3:8b                   # Chat-Modell
OLLAMA_EMBED_MODEL=qwen3-embedding:4b   # Embedding-Modell
EMBEDDING_BACKEND=ollama                # 'ollama' oder 'hf'
LLM_BACKEND=ollama                      # 'ollama' oder 'vllm'
ENV=local                               # 'local' oder 'docker'
TOP_K=5                                 # Retrieval Top-K
RRF_K=60                                # Reciprocal Rank Fusion
```

</details>

| Zugang | URL |
|:---|:---|
| 🖥️ **Frontend** | http://localhost:3000 |
| 📡 **API Docs** | http://localhost:8080/docs |
| ❤️ **Health Check** | http://localhost:8080/health |

---

## Nutzung

### Typischer Ablauf im Chat

```
1. Prozess auswählen    →  Kontext-Selektor im Chat
2. Position & Rolle     →  Aktuelle Prozessstellung definieren
3. Frage stellen        →  Natürlichsprachliche Prozessfrage
4. Antwort prüfen       →  Quellen, Begründung, Confidence Badge
```

### Scope-Modi

| Scope | Zweck | Gating-Modus |
|:---|:---|:---|
| 📄 **Dokumente** | Dokumentzentrierte Recherche ohne lokale Prozesssicht | `DOCS_ONLY` |
| 🔀 **Prozess** | Überblick über einen gesamten Prozess | `PROCESS_CONTEXT` |
| 📍 **Schritt** | Fokussierte Unterstützung an konkreter Prozessposition | `GATING_ENABLED` |

### API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|:---|:---|:---|
| `/health` | `GET` | Health Check |
| `/api/qa/ask` | `POST` | Frage-Antwort (Streaming/SSE) |
| `/api/search` | `POST` | Hybrid-Suche (BM25 + Vektor) |
| `/api/ingestion` | `POST` | Dokument-Upload & Indexierung |
| `/api/bpmn` | `POST` | BPMN 2.0 Import |
| `/api/whitelist` | `GET/POST` | Prozess-Whitelist verwalten |

---

## Reproduzierbarkeit und Evaluation

Dieses Repository ist als **ablationsfähiges Forschungsartefakt** aufgebaut. Pro Konfiguration werden Antworten, Retrieval-Resultate, Zitationen und Metriken persistiert.

### Datensätze

| Datensatz | *n* | Hypothese |
|:---|---:|:---|
| **Demo** | 16 | H1: Vergleich der Retrieval-Varianten |
| **Synthetic** | 31 | H1: Retrieval auf synthetischen Queries |
| **Demo_h2** | 10 | H2: Prozessverletzungen mit/ohne Gating |
| **Demo_h3** | 10 | H3: Verhalten in Grauzonen |
| **User Study** | 3 | H4: SUS und qualitative Wahrnehmung |

### Bewertungsdimensionen

| Dimension | Metriken |
|:---|:---|
| **Retrieval** | Recall@k, nDCG@k, MRR@k |
| **Generierung** | Semantic Similarity, ROUGE-L, BERTScore, Answer Relevance |
| **Faithfulness** | LLM-Judge, Quellenbezug, Attribution |
| **Prozesskonformität** | Whitelist-Verstöße, Gating-Metriken |
| **Usability** | SUS + qualitative SME-Einschätzungen |

### CLI-Referenz

<details>
<summary><strong>Alle Befehle anzeigen</strong></summary>

```bash
cd server

# ─── Setup ───────────────────────────────────────────────
python -m app.eval.runner initdb                          # DB-Schema anlegen
python -m app.eval.runner load-dataset demo \
    datasets/demo_queries.jsonl datasets/demo_qrels_1800.jsonl
python -m app.eval.runner load-queries demo \
    datasets/demo_queries.jsonl                            # Nur Queries (z.B. H2)
python -m app.eval.runner load-answers demo \
    datasets/demo_answers.jsonl                            # Gold-Antworten (EM/F1)

# ─── Experimente ─────────────────────────────────────────
python -m app.eval.runner run configs/baseline.yaml
python -m app.eval.runner run configs/baseline.yaml --repeats 3
python -m app.eval.runner study configs/study_ofat.yaml
python -m app.eval.runner study configs/hypotheses/study_h1_demo.yaml
python -m app.eval.runner study configs/study_h2_gating.yaml
python -m app.eval.runner study configs/study_gso_llm_prompt.yaml

# ─── Auswertung ──────────────────────────────────────────
python -m app.eval.runner score BASELINE
python -m app.eval.runner score BASELINE --reload-gold
python -m app.eval.runner report RUN_NAME --baseline BASELINE --out-dir reports
python -m app.eval.runner compare RUN_A RUN_B --metric recall@5 --iters 2000
```

</details>

### YAML-Konfigurationen

| Datei | Beschreibung |
|:---|:---|
| `configs/baseline.yaml` | Standard-Baseline (Hybrid, HF-Embeddings, Qwen3:8B) |
| `configs/enhanced_baseline.yaml` | GSO-optimierte Baseline (Semantic Chunking, CoT) |
| `configs/study_ofat.yaml` | OFAT-Ablation (Embedding, Chunking, LLM, Prompt) |
| `configs/study_h2_gating.yaml` | H2: Gating-Modi (none / process_context / gating) |
| `configs/hypotheses/study_h1_demo.yaml` | H1: Retrieval-Modi (hybrid / vector / bm25) |
| `configs/hypotheses/h3_gray_zone.yaml` | H3: Gray-Zone-Handling |
| `configs/study_gso_*.yaml` | GSO-Schritte (Top-K, LLM, Prompt, Reranking) |

---

## Projektstruktur

<details>
<summary><strong>Repository-Baum anzeigen</strong></summary>

```
Process-Aware-RAG-Chatbot/
├── client/                       # Frontend (Next.js 16)
│   ├── app/                      #   App Router (Pages & API Routes)
│   ├── components/               #   UI-Komponenten (feature/ + ui/)
│   ├── hooks/                    #   Custom React Hooks
│   ├── lib/                      #   Utilities & Konfiguration
│   ├── types/                    #   TypeScript Type Definitions
│   └── Dockerfile                #   Multi-Stage Production Build
│
├── server/                       # Backend (FastAPI / Python)
│   ├── app/
│   │   ├── core/                 #   Config, Guardrails, Prompt Builder, Auth
│   │   ├── services/             #   Retrieval, Gating, BPMN, LLM, Reformulation
│   │   ├── routers/              #   API-Endpunkte (qa, bpmn, ingestion, search)
│   │   ├── eval/                 #   Evaluations-Framework (Runner, Metrics, Reports)
│   │   └── main.py               #   FastAPI Entry Point
│   ├── configs/                  #   Experiment-Konfigurationen (YAML)
│   ├── datasets/                 #   Evaluations-Datensätze (JSONL)
│   ├── db/init/                  #   PostgreSQL Schema
│   ├── requirements.txt          #   Python Dependencies
│   ├── dockerfile                #   Backend Docker Image (CUDA)
│   └── docker-compose.yml        #   Dev-Infrastruktur (6 Services)
│
├── deploy/                       # Deployment-Skripte (PowerShell)
├── docs/                         # Thesis-Dokumentation & Architektur
├── .github/workflows/            # CI/CD (Build → GHCR)
├── docker-compose.prod.yml       # Production Stack (9 Services)
└── .env.production               # Production Environment Variables
```

</details>

---

## Entwicklung

### Backend

```bash
cd server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload  # Dev-Server
docker compose up -d          # Infrastruktur starten
docker compose logs -f redis   # Service-Logs
docker compose down            # Infrastruktur stoppen
```

| Variable | Beschreibung | Default |
|:---|:---|:---|
| `ENV` | `local` / `docker` — passt Service-URLs an | `local` |
| `OLLAMA_MODEL` | Chat-Modell | `qwen3:8b` |
| `EMBEDDING_BACKEND` | `hf` / `ollama` | `ollama` |
| `LLM_BACKEND` | `ollama` / `vllm` | `ollama` |
| `QA_FRAMEWORK` | `LC` (LangChain) / `LI` (LlamaIndex) | `LC` |

### Frontend

```bash
cd client
npm run dev        # http://localhost:3000
npm run build      # Production Build
npm run lint       # ESLint
```

<details>
<summary><strong>Debug-Befehle für Infrastruktur-Services</strong></summary>

```bash
# Redis Streams
docker exec -it <redis> redis-cli XINFO STREAM doc.uploaded
docker exec -it <redis> redis-cli XINFO GROUPS doc.uploaded

# OpenSearch
curl -s http://localhost:9200/_cat/indices?v
curl -s http://localhost:9200/chunks/_mappings

# Qdrant
curl -s http://localhost:6333/collections

# Ollama
docker exec -it <ollama> ollama list
docker exec -it <ollama> ollama pull qwen3:8b
```

</details>

---

## Production Deployment

### Windows (automatisiert)

```powershell
.\deploy\setup-windows.ps1       # Prerequisites prüfen
.\deploy\start.ps1               # Stack starten (9 Services)
.\deploy\start.ps1 -Pull         # Mit Image-Updates
.\deploy\stop.ps1                # Stack stoppen
```

### Manuell

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f
```

> **Production Stack:** Cloudflare Tunnel · Watchtower · Next.js · FastAPI · PostgreSQL · Redis · OpenSearch · Qdrant · Neo4j · Ollama

---

## Limitierungen

> Dieses Repository soll ein **ehrlich dokumentiertes Forschungsartefakt** sein. Dazu gehören die aktuellen Grenzen:

| Bereich | Limitation |
|:---|:---|
| **Systemrolle** | Research-Prototyp — ersetzt weder Fachverfahren noch Workflow-Management |
| **Grauzonen** | H3 zeigt: Prompt-Regeln allein verhindern Spekulation nicht zuverlässig |
| **Gating** | Prompt-Level Gating hilft, ist aber nicht in allen Fällen hart durchgesetzt |
| **Confidence** | Heuristische Evidenzstärke, keine kalibrierte Wahrscheinlichkeit |
| **User Study** | Explorativ — SUS und qualitative Bewertungen basieren auf kleiner Stichprobe (*n* = 3) |
| **Latenz** | Reranking und HyDE zeigen Potenzial, aber in Default-Baseline aus Laufzeitgründen deaktiviert |

---

## Zitieren

### Software-Artefakt

```bibtex
@software{alabdullah_neurapath_2026,
  author = {Ahmad Alabdullah},
  title  = {NeuraPath: Process-Aware RAG Chatbot},
  year   = {2026},
  url    = {https://github.com/Ahmad-Alabdullah/Process-Aware-RAG-Chatbot}
}
```

### Thesis

```bibtex
@thesis{alabdullah_2026_chatbot,
  author = {Ahmad Alabdullah},
  title  = {Chatbot für eine Hochschulverwaltung: Unterstützung von
            Mitarbeitenden und Professoren in Hochschulprozessen},
  school = {Hochschule Karlsruhe – University of Applied Sciences},
  type   = {Bachelorarbeit},
  year   = {2026}
}
```

---

## Mitwirken

Beiträge sind willkommen!

```bash
git checkout -b feature/mein-neues-feature
git commit -m "feat: Beschreibung des neuen Features"
git push origin feature/mein-neues-feature
# → Pull Request mit Begründung eröffnen
```

---

## Weiterentwicklung

### 🏛️ Konzept Produktivbetrieb (RQ2)

Die Thesis skizziert ein Betriebskonzept, das über den Prototyp hinausgeht — nicht nur Pipeline, sondern Governance:

**Rollenmodell:**

| Rolle | Verantwortung |
|:---|:---|
| **Endnutzer** | Fragen stellen, Feedback geben, Grauzonenwissen vorschlagen |
| **Prozessverantwortliche** | Grauzonen-Beiträge prüfen/freigeben, Akzeptanzkriterien definieren |
| **Systembetrieb** | Deployment, Monitoring, Modell-Updates, Incident Handling |
| **Datenschutz** | Datenflüsse prüfen, Logging-Konzept, Berechtigungsmapping |

**Berechtigungen** auf zwei Ebenen: *Prozess-/Schritt-Ebene* (Whitelist je Rolle) und *Dokument-/Chunk-Ebene* (rollenbasierter Zugriff auf Chunks).

**Grauzonen-Governance:** Endnutzer können informelles Wissen eintragen → Freigabe-Workflow durch Prozessverantwortliche → Indexierung als markierter Chunk (`TAG: GRAUZONE`) → transparente Anzeige in Quellenübersicht.

**Qualitätssteuerung:** Modell-Upgrades als kontrollierter Release-Prozess mit Offline-Regressionstests, definierten Abnahmekriterien und Rollback-Fähigkeit. Monitoring via Telemetrie (Deferral-Rate, Guardrail-Fallbacks, Prozessverletzungen) und Nutzerfeedback.

---

Basierend auf den Ergebnissen (Kapitel 9):

### 📊 Qualitätssteuerung & Daten

| Bereich | Beschreibung |
|:---|:---|
| **Domänendatensatz** | Realitätsnaher Datensatz durch Prozessverantwortliche — Grundlage für Regressionstests und Abnahmekriterien |
| **Grauzonen-Governance** | Kontrollierte, freigegebene Grauzonen-Chunks statt rein promptbasierter Regeln |
| **Leistungsfähigere LLMs** | Evaluation stärkerer lokaler Modelle, bevor architekturelle Änderungen priorisiert werden |

### 🏗️ Architektur & Features

| Bereich | Beschreibung |
|:---|:---|
| **Agentic RAG** | Iterative RAG-Loops zur Evidenznachforderung und Antwortverifikation |
| **Model Context Protocol** | Kontrollierte Anbindung interner Systeme über auditierbare MCP-Schnittstellen |
| **vLLM Backend** | Höherer Durchsatz durch Continuous Batching |
| **Adaptive Prompting** | Automatische Prompt-Stil-Wahl je nach Query-Komplexität |

---

## Lizenz

Dieses Projekt ist unter der **[MIT-Lizenz](LICENSE)** lizenziert.

---

<p align="center">
  <strong>Ahmad Alabdullah</strong> · <a href="https://github.com/Ahmad-Alabdullah">GitHub</a>
</p>
<p align="center">
  <sub>Mit ❤️ entwickelt als Teil einer Bachelorarbeit an der Hochschule Karlsruhe – Technik und Wirtschaft, WS 2025/26.</sub>
</p>
