# AI-Powered Research Paper Generation System

A comprehensive, production-ready framework for autonomous AI-driven academic research that integrates specialized research agents, literature analysis, ethical governance, and a modern web interface for paper generation.

## 🎯 Overview

This system leverages an agentic swarm approach to conduct complete academic research and generate comprehensive research papers. It combines:

- **5 Specialized Research Agents** for different aspects of academic research
- **Literature Intelligence** with automatic paper retrieval from ArXiv and Semantic Scholar
- **Intelligent Paper Generation** producing 20-30 page papers with 6 comprehensive sections
- **Ethics & Compliance Monitoring** with automated compliance scoring
- **Modern Web Dashboard** with real-time progress tracking and analytics
- **Full Backend API** for programmatic access to all research capabilities

## ✨ Key Features

### Research Paper Generation
- ✅ Generates **20-30 page papers** (~13,500 tokens per paper)
- ✅ **6 Required Sections**: Abstract, Introduction, Methodology, Results, Discussion, Conclusion
- ✅ Retrieves **20+ academic papers** per topic for comprehensive citations
- ✅ Comprehensive subsections within each major section
- ✅ Professional formatting with bibliography

### Specialized Research Agents
1. **Literature Agent** - Conducts comprehensive literature reviews with paper analysis
2. **Hypothesis Agent** - Generates research hypotheses and problem statements
3. **Methodology Agent** - Designs research methodologies and approaches
4. **Data Agent** - Processes and analyzes research data
5. **Ethics Agent** - Ensures ethical compliance and governance

### Ethical Compliance & Governance
- ✅ **Automated compliance scoring** (0-100%)
- ✅ **Multiple compliance categories**:
  - Data Privacy (GDPR compliance, data anonymization)
  - Responsible AI (bias detection, fairness assessment)
  - Research Integrity (reproducibility, citation accuracy)
- ✅ Real-time compliance monitoring during research
- ✅ Detailed audit trails for all research sessions

### Web-Based Dashboard
- ✅ **Modern, responsive UI** with animated components
- ✅ **Real-time metrics** - originality, novelty, plagiarism, ethics scores
- ✅ **Research sessions tracking** with progress visualization
- ✅ **Settings management** for user preferences and research configurations
- ✅ **Ethics dashboard** showing compliance reports
- ✅ **Results viewer** for completed research papers
- ✅ Gradient animations, floating orbs, glow effects, and smooth transitions

### Backend API
- ✅ RESTful API endpoints for all research operations
- ✅ Session management for tracking research progress
- ✅ Metrics and analytics endpoints
- ✅ Download papers in PDF, LaTeX, or BibTeX formats
- ✅ CORS support for frontend integration

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (for backend)
- Node.js 16+ (for frontend)
- API keys for LLM providers (OpenAI or Anthropic)

### 1. Clone and Set Up Environment

```bash
# Clone the repository
git clone <repo-url>
cd Agents

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys (see below for details)
```

### Required API Keys

| Variable | Description | How to Get |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | OpenAI API key | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | https://console.anthropic.com/settings/keys |
| `LLM_PROVIDER` | Provider: `openai` or `anthropic` | Set to your preferred provider |
| `LLM_MODEL` | Model name (e.g., `gpt-4`, `claude-3-sonnet-20240229`) | Choose based on provider |

### Optional API Keys

| Variable | Description | Notes |
|----------|-------------|-------|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API access | Optional; unauthenticated access available with rate limits |

### 3. Start the Application

```bash
# Terminal 1: Start backend API
cd d:\Google\Agents
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend development server
cd d:\Google\Agents\frontend
npm install
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📊 System Architecture

### Frontend (React + TypeScript + Vite)
- Modern, responsive dashboard with Tailwind CSS
- Real-time progress tracking with animations
- Research session management
- Settings and preferences interface
- Ethics compliance viewer

### Backend (FastAPI + Python)
- RESTful API server
- Research session management
- Agent orchestration and execution
- Metrics calculation and tracking
- Compliance scoring and monitoring

### Research Pipeline
```
User Request
    ↓
[Literature Agent] → Search ArXiv/Semantic Scholar → Retrieve 20+ papers
    ↓
[Hypothesis Agent] → Generate research questions and hypotheses
    ↓
[Methodology Agent] → Design research approach and methodology
    ↓
[Data Agent] → Process and analyze research data
    ↓
[Writing Agent] → Compose final 20-30 page paper with 6 sections
    ↓
[Ethics Agent] → Conduct compliance review and scoring
    ↓
Generated Research Paper (PDF/LaTeX)
```

## 📁 Project Structure

```
Agents/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── tasks.py             # Background task management
│   ├── requirements.txt      # Python dependencies
│   └── tests/               # Backend tests
├── frontend/
│   ├── src/
│   │   ├── pages/           # Page components (Dashboard, Results, etc.)
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/           # React hooks for data fetching
│   │   ├── lib/             # Utilities and API client
│   │   └── types/           # TypeScript type definitions
│   ├── package.json         # Node.js dependencies
│   └── vite.config.ts       # Vite configuration
├── src/
│   ├── agents/              # Research agent implementations
│   ├── authorship/          # Paper building and composition
│   ├── ethics/              # Ethical compliance evaluation
│   ├── originality/         # Plagiarism and novelty detection
│   ├── publication/         # Paper publishing utilities
│   ├── tools/               # Tool orchestration
│   └── utils/               # Configuration and logging
├── requirements.txt         # Main Python dependencies
└── README.md               # This file
```

## 🎓 Usage Guide

### Creating a Research Session

1. **Navigate to Dashboard** - View system overview and active sessions
2. **Click "New Research"** - Start a new research project
3. **Enter Research Topic** - Provide:
   - Topic title (e.g., "Deep Learning in Medical Imaging")
   - Research domain (e.g., "AI", "Medical Science")
   - Keywords for focused research
   - Complexity level (Basic, Intermediate, Advanced)
4. **Submit** - System automatically:
   - Retrieves 20+ relevant papers
   - Generates research hypotheses
   - Designs methodology
   - Analyzes and synthesizes data
   - Composes comprehensive paper
   - Evaluates ethics compliance

### Monitoring Progress

- **Dashboard** - Real-time metrics and agent status
- **Sessions** - View all active and completed research sessions
- **Results** - Download and view generated papers
- **Ethics** - Review compliance reports and scores

### Downloading Results

Generated papers are available in multiple formats:
- **PDF** - Professional formatted document
- **LaTeX** - Source file for further editing
- **BibTeX** - Bibliography data for reference management

## 📊 Paper Specifications

Each generated paper includes:
- **Abstract** (400 tokens) - Executive summary of research
- **Introduction** (2,800 tokens) - Background, context, 6+ citations
- **Methodology** (3,500 tokens) - Detailed research approach
- **Results** (2,800 tokens) - Data analysis and findings
- **Discussion** (3,200 tokens) - Interpretation and implications
- **Conclusion** (800 tokens) - Summary and future directions
- **References** - 20+ academic sources with proper citations
- **Total**: 13,500 tokens (~10,000 words = 20+ pages)

## 🔐 Security & Privacy

- **Data Privacy**: GDPR-compliant data handling
- **API Key Security**: Keys stored in environment variables
- **Session Isolation**: Each research session is independently managed
- **Compliance Monitoring**: Automatic ethics evaluation
- **Audit Trails**: Complete tracking of research activities

## 📈 Performance Metrics

The system tracks and reports:
- **Originality Score** - Plagiarism detection (0-100%)
- **Novelty Score** - Uniqueness of research contributions (0-100%)
- **Ethics Score** - Compliance rating (0-100%)
- **Plagiarism Detection** - Low scores indicate original work
- **Agent Performance** - Task completion and execution time

## 🧪 Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/

# Run frontend tests
cd frontend
npm test
```

All 117+ property-based tests are included to verify:
- Agent functionality
- API endpoints
- Data processing
- Ethics compliance
- Error handling

## 🛠️ Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_PROVIDER=openai                    # or 'anthropic'
LLM_MODEL=gpt-4                        # or specific model name
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# API Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Research Settings
MAX_PAPERS_PER_TOPIC=20                # Number of papers to retrieve
PAPER_TOKEN_LIMIT=13500                # Total tokens for paper generation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or suggestions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include system specifications and error messages
4. Attach relevant logs from `backend.log` or browser console

## 🔄 Recent Updates (December 2025)

### Version 2.0 - UI Enhancement Release
- ✨ Modern, animated frontend with gradient headers
- ✨ Floating background orbs and glow card effects
- ✨ Real-time metrics dashboard
- ✨ Enhanced Settings page with user preferences
- ✨ Complete Ethics & Compliance dashboard
- ✨ Improved error handling and recovery actions
- ✨ Fixed backend API endpoints for settings and compliance
- 🐛 Fixed JSX syntax errors and component structure
- 🚀 Optimized agent performance and paper generation
- 📊 Enhanced metrics tracking and reporting

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **Component Library**: Check `frontend/src/components/` for reusable UI components
- **Agent Implementation**: See `src/agents/swarm.py` for research agent details
- **Type Definitions**: `frontend/src/types/index.ts` for data structures

## 🎨 Design System

Frontend uses:
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS with custom animations
- **UI Components**: Shadcn/ui component library
- **Animations**: Framer Motion for smooth transitions
- **Colors**: oklch color palette (primary, secondary, accent)
- **Icons**: Lucide React icon library

---

**Happy researching! 🚀📚**
