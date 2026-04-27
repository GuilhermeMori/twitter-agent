# Backend Setup Guide

This document provides detailed instructions for setting up the Twitter Scraping SaaS Platform backend.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Redis server (for Celery task queue)
- Supabase account (for database and storage)

## Quick Start

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

For development (includes testing and linting tools):
```bash
pip install -r requirements-dev.txt
```

### 3. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and configure the following:

#### Required Configuration

**Supabase**:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key

**Encryption**:
- `ENCRYPTION_KEY`: Generate with:
  ```bash
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```

**Redis** (if not using default):
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)

#### Optional Configuration

- `DEBUG`: Set to `True` for development
- `CORS_ORIGINS`: List of allowed origins for CORS

### 4. Start Redis

If Redis is not running, start it:

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using system package manager
# Ubuntu/Debian
sudo systemctl start redis-server

# macOS
brew services start redis
```

### 5. Run the Application

#### Start API Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

#### Start Celery Worker

In a separate terminal:

```bash
celery -A src.workers.celery_app worker --loglevel=info
```

## Using Docker Compose

For a complete development environment with all services:

```bash
docker-compose up
```

This will start:
- FastAPI server on port 8000
- Celery worker
- Redis on port 6379

## Project Structure

```
backend/
├── src/                      # Source code
│   ├── api/                  # API layer
│   │   └── routes/           # API route modules
│   ├── core/                 # Core utilities
│   │   └── config.py         # Configuration management
│   ├── models/               # Data models
│   │   ├── campaign.py       # Campaign models
│   │   └── configuration.py  # Configuration models
│   ├── repositories/         # Data access layer
│   ├── services/             # Business logic
│   ├── workers/              # Celery workers
│   │   └── celery_app.py     # Celery configuration
│   └── main.py               # Application entry point
├── tests/                    # Test suite
│   ├── conftest.py           # Pytest fixtures
│   └── test_main.py          # Basic tests
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── pyproject.toml            # Project configuration
├── setup.py                  # Package setup
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── Makefile                  # Common tasks
└── README.md                 # Project documentation
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Using Makefile

Common tasks are available via Makefile:

```bash
make install      # Install production dependencies
make install-dev  # Install development dependencies
make run          # Run FastAPI server
make worker       # Run Celery worker
make test         # Run tests
make coverage     # Run tests with coverage
make lint         # Run linters
make format       # Format code
make clean        # Clean generated files
```

## API Documentation

Once the server is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Import Errors

If you encounter import errors, ensure you're running commands from the `backend/` directory and the virtual environment is activated.

### Redis Connection Errors

Ensure Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Supabase Connection Errors

Verify your Supabase credentials in `.env`:
- Check that `SUPABASE_URL` is correct
- Ensure `SUPABASE_KEY` is the anon/public key (not the service role key for development)

### Dependency Conflicts

If you encounter dependency version conflicts, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## Next Steps

After completing the setup:

1. **Configure Supabase Database**: Create the required tables (see database schema in design.md)
2. **Set up Supabase Storage**: Create a bucket for document storage
3. **Implement API Routes**: Add endpoints for configuration and campaigns
4. **Implement Services**: Add business logic for campaign execution
5. **Implement Workers**: Add Celery tasks for asynchronous processing

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Supabase Documentation](https://supabase.com/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
