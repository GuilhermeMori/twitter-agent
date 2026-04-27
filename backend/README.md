# Twitter Scraping SaaS Platform - Backend

Python backend for the Twitter Scraping SaaS Platform, built with FastAPI, Celery, and Supabase.

## Features

- **FastAPI REST API**: High-performance async API
- **Celery Workers**: Asynchronous task processing for campaigns
- **Supabase Integration**: PostgreSQL database and file storage
- **Twitter Scraping**: Integration with Apify for Twitter data collection
- **OpenAI Analysis**: Content analysis using OpenAI API
- **Document Generation**: Automated .doc file generation
- **Email Notifications**: SMTP-based email delivery

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Task Queue**: Celery 5.3+ with Redis
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage
- **Python**: 3.9+

## Project Structure

```
backend/
├── src/
│   ├── api/              # API routes and endpoints
│   │   └── routes/       # Route modules
│   ├── core/             # Core utilities and configuration
│   ├── models/           # Pydantic models and schemas
│   ├── repositories/     # Data access layer
│   ├── services/         # Business logic services
│   ├── workers/          # Celery workers and tasks
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── pyproject.toml        # Project configuration
└── setup.py              # Package setup
```

## Setup

### Prerequisites

- Python 3.9 or higher
- Redis server
- Supabase account

### Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

For development:
```bash
pip install -r requirements-dev.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Generate encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Running the Application

### Start the API server:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Celery worker:
```bash
celery -A src.workers.celery_app worker --loglevel=info
```

### Start Celery beat (for scheduled tasks):
```bash
celery -A src.workers.celery_app beat --loglevel=info
```

## Development

### Run tests:
```bash
pytest
```

### Run tests with coverage:
```bash
pytest --cov=src --cov-report=html
```

### Format code:
```bash
black src/ tests/
```

### Lint code:
```bash
flake8 src/ tests/
```

### Type checking:
```bash
mypy src/
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

The backend follows a layered architecture:

1. **API Layer** (`api/`): FastAPI routes and request/response handling
2. **Service Layer** (`services/`): Business logic and orchestration
3. **Repository Layer** (`repositories/`): Data access and persistence
4. **Worker Layer** (`workers/`): Asynchronous task processing
5. **Core Layer** (`core/`): Shared utilities and configuration

## Key Components

- **Configuration Manager**: Secure credential storage with encryption
- **Campaign Service**: Campaign creation and management
- **Campaign Executor**: Asynchronous campaign execution (Celery task)
- **Scraping Engine**: Twitter scraping via Apify
- **Analysis Engine**: Content analysis with OpenAI
- **Document Generator**: .doc file generation
- **Email Service**: Email notifications with attachments
- **Storage Service**: File management with Supabase Storage

## Testing

The project uses:
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **hypothesis**: Property-based testing
- **pytest-cov**: Coverage reporting

## License

[Your License Here]
