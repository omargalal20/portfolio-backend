# Portfolio Backend

A FastAPI-based backend service for my portfolio website.

## Architecture Overview

The application is structured with the following components:

- **PortfolioAgent**: Main agent class that handles RAG functionality and response generation
- **OrchestratorService**: Manages the FastRTC stream and audio processing
- **FastAPI App**: Web server that mounts the voice stream and provides REST APIs

## Setup Instructions

### 1. Environment Variables

Create a `.env` file with the following variables:

```env
ENVIRONMENT=production
APP_NAME=Portfolio Backend
APP_VERSION=1.0.0
APP_PORT=8000

# Agent Configuration
AGENT_ID=gemini-1.5-flash
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=4096
AGENT_TOP_P=0.9
AGENT_TOP_K=40

# API Keys
GOOGLE_API_KEY=your_google_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
PINECONE_API_KEY=your_pinecone_api_key
HF_TOKEN=your_huggingface_token

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1

# Cloudflare TURN Configuration
CLOUDFLARE_TURN_KEY_ID=your_turn_key_id
CLOUDFLARE_TURN_KEY_API_TOKEN=your_turn_key_token

# Vector Store Configuration
PINECONE_INDEX_NAME=your_pinecone_index

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# LangSmith Configuration
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=portfolio-agent
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 3. Test the Setup

Run the test script to verify everything is working:

```bash
python test_portfolio_agent.py
```

### 4. Run the Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- **Voice Stream**: `/stream` - WebRTC voice interface
- **Health Check**: `/api/v1/health` - Application health status
- **Ingestion**: `/api/v1/ingestion` - Data ingestion endpoints
