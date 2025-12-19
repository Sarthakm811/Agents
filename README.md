# README.md

# Hybrid AI Research System

A modular, production‑ready framework for autonomous AI‑driven research that integrates originality guardrails, agentic swarms, tool orchestration, authorship management, and ethical governance.

## Features
- Originality verification (plagiarism detection, novelty scoring)
- Swarm of specialized research agents
- Autonomous tool orchestration for literature search, data generation, analysis, etc.
- End‑to‑end paper composition with authorship attribution
- Ethical compliance and transparency reporting
- Configurable via YAML files

## Quick Start

### 1. Clone and Set Up Environment

```bash
# Clone the repo
git clone <repo-url>
cd hybrid-research-system

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

The system requires API keys to connect to LLM providers and academic databases.

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
```

#### Required API Keys

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Yes (if using OpenAI) |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | Yes (if using Anthropic) |
| `LLM_PROVIDER` | LLM provider to use: `openai` or `anthropic` | Yes (default: `openai`) |
| `LLM_MODEL` | Model name (e.g., `gpt-4`, `claude-3-sonnet-20240229`) | Yes (default: `gpt-4`) |

#### Optional API Keys

| Variable | Description | Notes |
|----------|-------------|-------|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API key | Optional. Without it, uses unauthenticated access with lower rate limits (100 requests per 5 minutes) |

#### Getting API Keys

- **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com) and create an API key at [API Keys](https://platform.openai.com/api-keys)
- **Anthropic**: Sign up at [console.anthropic.com](https://console.anthropic.com) and create an API key at [Settings > Keys](https://console.anthropic.com/settings/keys)
- **Semantic Scholar**: Request an API key at [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api)

### 3. Run the Application

```bash
# Start the backend server
cd backend
python main.py

# In a separate terminal, start the frontend
cd frontend
npm install
npm run dev
```

The API will be available at `http://localhost:8000` and the frontend at `http://localhost:5173`.

## Configuration

### Environment Variables

All configuration is done through environment variables. See `.env.example` for a complete list with descriptions.

### Rate Limits

The system respects external API rate limits:
- **arXiv**: 1 request per 3 seconds
- **Semantic Scholar**: 100 requests per 5 minutes (unauthenticated)
- **LLM APIs**: Token-based limits per provider

## Project Structure

```
hybrid-research-system/
├── backend/           # FastAPI backend server
├── frontend/          # React frontend application
├── src/
│   ├── agents/        # Research agents and LLM client
│   ├── authorship/    # Paper building and composition
│   ├── core/          # Core hybrid system
│   ├── ethics/        # Ethical governance
│   ├── originality/   # Plagiarism and novelty checks
│   ├── publication/   # Publication packaging
│   ├── tools/         # Tool orchestration
│   └── utils/         # Configuration and utilities
└── notebooks/         # Jupyter notebooks for testing
```
