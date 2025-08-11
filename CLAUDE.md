# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Backend (FastAPI)
- **Start backend**: `cd backend && python -m app.main` or `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Install dependencies**: `cd backend && pip install -r requirements.txt`
- **Start database**: `cd backend && docker-compose up -d`
- **Test database connection**: Visit `http://localhost:8000/debug/test-db`
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)

### Frontend (React + TypeScript)
- **Start frontend**: `cd frontend && npm start`
- **Install dependencies**: `cd frontend && npm install`
- **Build for production**: `cd frontend && npm run build`
- **Run tests**: `cd frontend && npm test`

### Development Workflow
- Backend runs on port 8000, frontend on port 3000
- Database: PostgreSQL on port 5432, Redis on port 6379
- Use `docker-compose ps` to check database status

## Architecture Overview

### Multi-Tenant SaaS Structure
- **Multi-tenancy**: Every database query includes `company_id` filtering for data isolation
- **Authentication**: JWT-based with mock auth (temporary) - real auth system needs implementation
- **Database**: PostgreSQL with async SQLAlchemy, includes audit trails and soft deletes

### Backend Architecture (FastAPI)
```
backend/app/
├── main.py           # FastAPI app entry point with middleware and routes
├── core/             # Core configuration and database
│   ├── config.py     # Environment settings with Pydantic validation
│   └── database.py   # Database connection and session management
├── models/           # SQLAlchemy database models
├── schemas/          # Pydantic request/response models  
├── services/         # Business logic layer
└── api/v1/           # HTTP endpoints (thin layer, delegates to services)
```

### Key Design Pattern
- **Services Pattern**: Business logic in services/ (e.g., campaign_services.py, email_services.py)
- **Repository Pattern**: Database operations abstracted through models
- **Dependency Injection**: Database sessions and auth dependencies in api/deps.py

### Frontend Architecture (React + TypeScript)
- **API Client**: Centralized in `src/services/api.js` with helper functions
- **Components**: Feature-based organization (e.g., `components/leads/`)
- **Styling**: Tailwind CSS with PostCSS configuration

## Key Business Logic

### Lead Management
- **Lead Scoring**: Automatic 0-100 scoring based on data completeness and quality indicators
- **Multi-tenant**: All leads filtered by `company_id`
- **Status Workflow**: new → qualified → contacted → converted → closed

### Campaign System
- **Email Generation**: Uses OpenAI API for personalized email content
- **Sequences**: Support for multi-step email campaigns with delays
- **Lead Filtering**: Campaigns can target leads by score, status, source, etc.

### Database Schema Key Points
- **Composite Indexes**: Optimized for multi-tenant queries (e.g., `company_id + status`)
- **JSON Fields**: Flexible storage for custom fields and research data
- **Audit Fields**: All models include created_at, updated_at, created_by
- **Soft Deletes**: Use `is_deleted` flag instead of actual deletion

## Development Environment

### Required Environment Variables (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (change in production)
- `OPENAI_API_KEY`: For email generation
- `DEBUG`: Set to `true` for development
- `ALLOWED_ORIGINS`: CORS origins (include frontend URL)

### Database Setup
1. Start containers: `docker-compose up -d`
2. Database auto-initializes on first FastAPI startup
3. Check health: `docker-compose ps`

## Testing and Debugging

### API Testing
- Interactive docs at `/docs` endpoint (development only)
- Health check at `/health`
- Debug endpoints at `/debug/settings` and `/debug/test-db` (development only)

### Common Issues
- **Import errors**: Ensure you're in backend/ directory with activated venv
- **Database connection**: Check PostgreSQL container status with `docker-compose ps`
- **CORS errors**: Verify frontend URL in `ALLOWED_ORIGINS` setting

## Future Development Notes

### Planned Features (TODOs in codebase)
- Real user authentication system (currently mock)
- MCP integration for Gmail, news sources
- AI agents for automated outreach
- Enhanced campaign scheduling and analytics

### Code Quality Standards
- Type hints required throughout Python code
- Pydantic models for all API contracts
- Async/await for all database operations
- Error logging with structured logging (structlog)
- Service layer pattern for business logic separation