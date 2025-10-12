# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This project follows a strict layered architecture:

### Service Layer (`src/services/`)
- Core business logic implementation
- Services are bound to a specific Model/Data Model
- Can make database queries and implement complex business logic
- Use the Service Provider pattern via `BaseServiceProvider` for extensible service registration
- Services extend `BaseService` or `BaseServiceWithDB` for database operations

### Route Layer (`src/routes/`)
- Thin HTTP/WebSocket transport layer
- Always delegates to services
- Never contains business logic
- Handles request/response transformation using schemas

### Model Layer (`src/models/`)
- Data structure representation using SQLModel
- Base classes in `src/models/base.py`:
  - `BaseModel`: Simple model with ID
  - `BaseModelWithTimestamp`: Adds created_at/updated_at
  - `BaseModelWithSoftDelete`: Adds soft delete capability with deleted_at
- Models include query helper methods (count, get, list, delete)

### Schema Layer (`src/schema/`)
- Input/output data validation using Pydantic
- Used by routes and services for data enrichment/stripping
- Separate from models to control external data exposure

### Configuration (`src/config/`)
- Settings split into logical groups in `settings.py`:
  - `ServerSettings`: Server and API configuration
  - `SecuritySettings`: Auth and security
  - `DatabaseSettings`: PostgreSQL connection (builds sqlalchemy_url)
  - `RedisSettings`: Redis/cache configuration
  - `EmailSettings`: SMTP settings
  - `OAuthSettings`: OAuth providers (Google)
- All settings loaded from `.env` file
- Database engines in `src/config/db/postgres.py` (sync and async)
- Alembic migrations in `src/config/db/alembic.py`

### Utilities (`src/lib/`)
- `src/lib/abstracts/`: Abstract base classes for services and providers
- `src/lib/utils/`: Utility functions (e.g., CORS parser)

## Common Commands

### Development Setup
```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --all-groups
```

### Running the Application
```bash
# Run development server
uv run uvicorn src.main:app --reload --host localhost --port 8000
```

### Code Quality
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

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_file.py

# Run with coverage
uv run coverage run -m pytest
uv run coverage report
```

### Database Migrations
```bash
# Create new migration (when Alembic is set up)
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Development Guidelines

### Adding New Features

1. **Model**: Create/update SQLModel in `src/models/` extending appropriate base class
2. **Schema**: Define Pydantic schemas in `src/schema/` for input/output validation
3. **Service**: Implement business logic in `src/services/` extending `BaseAsyncServiceWithDB` (preferred) or `BaseServiceWithDB`
   - Use `AsyncSession` and `async def` methods
   - Import: `from src.services.base import BaseAsyncServiceWithDB`
4. **Route**: Add HTTP endpoints in `src/routes/` that delegate to services
   - FastAPI routes should be `async def` to work with async services

### Service Provider Pattern

When creating extensible services that support multiple implementations:

```python
from src.lib.abstracts import BaseService, BaseServiceProvider

class MyService(BaseService):
    def __init__(self, config: str):
        self.config = config

class MyServiceProvider(BaseServiceProvider):
    _services = {
        "implementation_a": MyServiceImplA,
        "implementation_b": MyServiceImplB,
    }

# Usage
provider = MyServiceProvider("implementation_a", config="value")
```

### Database Sessions

**Async-First Approach (Preferred):**
- **Always prioritize async methods** for all service implementations
- Import: `from src.config.db.postgres import AsyncSession, make_async_session`
- Services extend `BaseAsyncServiceWithDB` and use `AsyncSession`
- All methods are `async def` with `await` for DB operations

**Sync Approach (Rare Cases Only):**
- Only use for specific cases requiring synchronous operations
- Import: `from src.config.db.postgres import Session, engine`
- Services extend `BaseServiceWithDB` and use `Session`
- If sync methods needed, create separate service (e.g., `SyncUserService`)

**Database Engines:**
- Async engine: `async_engine` from `src.config.db.postgres`
- Sync engine: `engine` from `src.config.db.postgres`
- Async session maker: `make_async_session` from `src.config.db.postgres`

### Database Service Operations

`BaseAsyncServiceWithDB` (preferred) and `BaseServiceWithDB` provide type-aware database operations that automatically adapt based on the model type.

**Type Checking:**
- Automatically detects if model supports soft delete via `_supports_soft_delete()` method
- Only applies soft delete logic when model extends `BaseModelWithSoftDelete`
- Works with all model types: `BaseModel`, `BaseModelWithTimestamp`, `BaseModelWithSoftDelete`

**Async Usage (Preferred):**
```python
from src.config.db.postgres import AsyncSession, make_async_session
from src.services.user import UserService

# Using async context manager
async with make_async_session() as session:
    # Get single record (excludes soft-deleted by default)
    user = await UserService.get(user_id, session)
    user_with_deleted = await UserService.get(user_id, session, with_deleted=True)

    # Get by email
    user = await UserService.get_by_email("user@example.com", session)

    # Create new user
    new_user = await UserService.create(user_data, session)

    # List records (excludes soft-deleted by default)
    users = await UserService.list(session)
    all_users = await UserService.list(session, include_deleted=True)

    # Count records
    count = await UserService.count(session)
    total_count = await UserService.count(session, include_deleted=True)

    # Soft delete (only works if model supports it)
    await UserService.delete(user, session, soft=True)

    # Hard delete (works for all models)
    await UserService.delete(user, session, soft=False)
```

**Sync Usage (Rare Cases):**
```python
from src.config.db.postgres import Session, engine

with Session(engine) as session:
    # Same methods but without await
    user = SyncUserService.get(user_id, session)
    users = SyncUserService.list(session)
```

**Important:** If your model doesn't extend `BaseModelWithSoftDelete`, the `deleted_at` filtering is automatically skipped, making the service work seamlessly with all model types.

### FastAPI Dependency Type Annotations

**IMPORTANT**: When defining FastAPI dependency type aliases, NEVER use the `type` keyword. Always use `TypeAlias` annotation instead.

**Correct:**
```python
from typing import Annotated, TypeAlias
from fastapi import Depends

DBSession: TypeAlias = Annotated[Session, Depends(get_db_session)]
AsyncDBSession: TypeAlias = Annotated[AsyncSession, Depends(get_async_db_session)]
SessionUser: TypeAlias = Annotated[User, Depends(get_session_user)]
```

**Incorrect:**
```python
# DO NOT USE - This breaks FastAPI dependency injection
type DBSession = Annotated[Session, Depends(get_db_session)]
type AsyncDBSession = Annotated[AsyncSession, Depends(get_async_db_session)]
```

The `type` keyword creates a generic alias that doesn't work properly with FastAPI's dependency injection system. Always use the `TypeAlias` annotation pattern for dependency type aliases.

## Configuration Notes

- All environment variables are defined in `.env`
- Settings validates required values and warns about insecure defaults
- PostgreSQL connection uses `postgresql+psycopg` driver
- Redis URL auto-built from components if not explicitly set
- CORS origins parsed from comma-separated string in `.env`