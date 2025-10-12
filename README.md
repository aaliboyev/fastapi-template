# FastAPI Template

A production-ready FastAPI template with PostgreSQL, Redis, and modern Python tooling. Built with best practices, strict layered architecture, and async-first approach.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Robust relational database with async support via psycopg
- **Redis** - In-memory data store for caching and sessions
- **SQLModel** - SQL databases in Python with Pydantic models
- **Pydantic** - Data validation using Python type annotations
- **Alembic** - Database migration tool
- **AuthX** - Authentication and authorization
- **Docker** - Containerized development and deployment
- **UV** - Fast Python package manager
- **Ruff** - Fast Python linter and formatter
- **MyPy** - Static type checking

## Project Structure

```
src/
├── api/                    # API layer
│   ├── deps/              # FastAPI dependencies
│   ├── middlewares/       # Custom middlewares
│   └── routes/            # API route definitions
├── config/                # Configuration and database setup
│   └── db/               # Database engines and sessions
├── lib/                   # Shared libraries and utilities
│   ├── abstracts/        # Abstract base classes
│   ├── memory/           # Memory/cache implementations
│   └── utils/            # Utility functions
├── models/                # SQLModel database models
├── schema/                # Pydantic schemas for validation
└── services/              # Business logic layer
```

## Architecture

This template follows a strict **layered architecture**:

### Service Layer (`src/services/`)
- Core business logic implementation
- Services extend `BaseAsyncServiceWithDB` for async database operations
- Type-aware database operations with automatic soft-delete support
- Example: `UserService`, `UserAccountService`

### Route Layer (`src/api/routes/`)
- Thin HTTP/WebSocket transport layer
- Always delegates to services
- Never contains business logic
- Handles request/response transformation using schemas

### Model Layer (`src/models/`)
- Data structure representation using SQLModel
- Base classes with progressive features:
  - `BaseModel`: Simple model with ID
  - `BaseModelWithTimestamp`: Adds created_at/updated_at
  - `BaseModelWithSoftDelete`: Adds soft delete with deleted_at
- Models include query helper methods

### Schema Layer (`src/schema/`)
- Input/output data validation using Pydantic
- Separate from models to control external data exposure
- Used by routes and services

## Quick Start

### Prerequisites

- Python 3.13+
- [UV](https://github.com/astral-sh/uv) package manager
- PostgreSQL (or use Docker Compose)
- Redis (or use Docker Compose)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd fastapi-template
```

2. Install dependencies:
```bash
uv sync --all-groups
```

3. Copy the example environment file:
```bash
cp .env.example .env
```

4. Update the `.env` file with your configuration:
```bash
# Edit .env with your settings
SECRET_KEY=your-secret-key-here
POSTGRES_DB=app
POSTGRES_USER=app
POSTGRES_PASSWORD=your-password
```

### Running with Docker Compose (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Start all services (PostgreSQL, Redis, and the API)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

The API will be available at `http://localhost:8000`.

### Running Locally

If you prefer to run the application locally:

1. Ensure PostgreSQL and Redis are running

2. Run database migrations:
```bash
uv run alembic upgrade head
```

3. Start the development server:
```bash
uv run uvicorn src.main:app --reload --host localhost --port 8000
```

4. Access the API:
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative API docs: http://localhost:8000/redoc

## Development

### Code Quality

This project uses [Just](https://github.com/casey/just) for task automation:

```bash
# Run all checks (format, lint, typecheck)
just check

# Run linter only
just lint

# Fix linting issues automatically
just fix

# Format code
just format

# Type checking
just typecheck
```

Or use UV directly:

```bash
# Linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run coverage run -m pytest
uv run coverage report

# Run specific test file
uv run pytest tests/test_file.py
```

### Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

## Configuration

All configuration is managed through environment variables in the `.env` file:

### Server Settings
- `ENVIRONMENT`: Environment (local, staging, production)
- `PROJECT_NAME`: Project name for API documentation
- `SERVER_HOST`: Server host (default: localhost)
- `SERVER_PORT`: Server port (default: 8000)
- `SERVER_PROTOCOL`: Protocol (http/https)

### Security Settings
- `SECRET_KEY`: Secret key for JWT tokens (change in production!)
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### Database Settings
- `POSTGRES_SERVER`: PostgreSQL server host
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password

### Redis Settings
- `REDIS_HOST`: Redis server host
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password (optional)

### Email Settings (Optional)
- `SMTP_HOST`: SMTP server host
- `SMTP_USER`: SMTP username
- `SMTP_PASSWORD`: SMTP password
- `EMAILS_FROM_EMAIL`: From email address
- `SMTP_PORT`: SMTP port (default: 587)

## Adding New Features

Follow this workflow when adding new features:

1. **Model**: Create/update SQLModel in `src/models/` extending appropriate base class
2. **Schema**: Define Pydantic schemas in `src/schema/` for input/output validation
3. **Service**: Implement business logic in `src/services/` extending `BaseAsyncServiceWithDB`
4. **Route**: Add HTTP endpoints in `src/api/routes/` that delegate to services
5. **Migration**: Create and apply database migrations with Alembic

### Example: Adding a Blog Feature

```python
# 1. Model (src/models/blog.py)
from src.models.base import BaseModelWithTimestamp

class BlogPost(BaseModelWithTimestamp, table=True):
    title: str
    content: str
    author_id: int

# 2. Schema (src/schema/blog.py)
from pydantic import BaseModel

class BlogPostCreate(BaseModel):
    title: str
    content: str
    author_id: int

# 3. Service (src/services/blog.py)
from src.services.base import BaseAsyncServiceWithDB

class BlogService(BaseAsyncServiceWithDB):
    model = BlogPost

    @classmethod
    async def create_post(cls, post_in: BlogPostCreate, session: AsyncSession):
        # Business logic here
        pass

# 4. Route (src/api/routes/blog.py)
from fastapi import APIRouter
from src.api.deps.db import AsyncDBSession

router = APIRouter()

@router.post("/posts")
async def create_blog_post(
    post_in: BlogPostCreate,
    db_session: AsyncDBSession
):
    return await BlogService.create_post(post_in, db_session)
```

## Production Deployment

### Environment Variables

Ensure you set secure values for production:

```bash
ENVIRONMENT=production
SECRET_KEY=<generate-a-secure-key>
FIRST_SUPERUSER_PASSWORD=<secure-password>
POSTGRES_PASSWORD=<secure-password>
```

### Docker

Build and run with Docker:

```bash
# Build the image
docker build -t fastapi-template:latest .

# Run with Docker Compose
docker-compose up -d
```

### Security Checklist

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Change all default passwords
- [ ] Configure CORS origins appropriately
- [ ] Enable HTTPS/SSL in production
- [ ] Review and configure rate limiting
- [ ] Set up proper logging and monitoring
- [ ] Configure database backups
- [ ] Review and update security headers

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run code quality checks (`just check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you have questions or need help:

- Open an issue on GitHub
- Check the [CLAUDE.md](CLAUDE.md) file for AI assistant guidance
- Review the FastAPI documentation: https://fastapi.tiangolo.com/

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [UV](https://github.com/astral-sh/uv)
- [Ruff](https://github.com/astral-sh/ruff)
