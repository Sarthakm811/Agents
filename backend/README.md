# Backend API Server

FastAPI backend that integrates with the Hybrid AI Research System.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The backend requires API keys to be set as environment variables. Copy the example file from the project root:

```bash
# From the project root directory
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required: Choose your LLM provider
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Required: Add the API key for your chosen provider
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Optional: Semantic Scholar API key for higher rate limits
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-key
```

### 3. Run the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

- `POST /api/sessions` - Create a new research session
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Get session details
- `POST /api/sessions/{id}/start` - Start a session
- `POST /api/sessions/{id}/pause` - Pause a session
- `POST /api/sessions/{id}/stop` - Stop a session
- `GET /api/sessions/{id}/results` - Get research results
- `GET /api/metrics` - Get overall metrics
- `GET /api/sessions/{id}/compliance` - Get compliance report