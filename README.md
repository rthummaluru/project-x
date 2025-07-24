# project-x
# 🚀 Sales Automation SaaS - MVP Backend

A FastAPI-based sales automation platform with AI agents and MCP integration.

## 📋 Features

- ✅ **Lead Management**: Create, update, and track leads with automatic scoring
- ✅ **Multi-tenant Architecture**: Secure data isolation per company
- ✅ **JWT Authentication**: Secure API access
- ✅ **Rate Limiting**: Built-in protection against abuse
- ✅ **Async Database**: High-performance PostgreSQL with SQLAlchemy
- 🔄 **MCP Integration**: Coming next - Gmail, Apollo, news sources
- 🔄 **AI Agents**: Coming next - Email generation and outreach

## 🏗️ Architecture Decisions Explained

### Why FastAPI?
- **Async Support**: Handle 1000+ concurrent users efficiently
- **Auto Documentation**: Swagger docs generated automatically
- **Type Safety**: Pydantic ensures data validation
- **Performance**: One of the fastest Python frameworks

### Why This Folder Structure?
- **models/**: Database schema (what data looks like)
- **schemas/**: API contracts (what goes in/out of endpoints)  
- **services/**: Business logic (how things work)
- **api/**: HTTP endpoints (where requests come in)

This separation makes testing easier and allows you to change one layer without affecting others.

### Multi-tenant Security
Every database query includes `company_id` filtering. Users can only access their company's data.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings
```

### 2. Start Database

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify databases are running
docker-compose ps
```

### 3. Run Application

```bash
# Start the API server
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

Visit http://localhost:8000/docs for interactive API documentation.

**Test creating a lead:**
```bash
curl -X POST "http://localhost:8000/api/v1/leads/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe", 
    "company_name": "Example Corp",
    "job_title": "VP of Sales",
    "source": "linkedin"
  }'
```

## 🗂️ Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API endpoints
│   │   ├── leads.py      # ✅ Lead CRUD operations
│   │   └── deps.py       # ✅ Authentication dependencies
│   ├── core/             # Core configuration
│   │   ├── config.py     # ✅ Environment settings
│   │   └── database.py   # ✅ Database connection
│   ├── models/           # Database models
│   │   └── lead.py       # ✅ Lead model with multi-tenancy
│   ├── schemas/          # API request/response models
│   │   └── lead.py       # ✅ Pydantic schemas
│   ├── services/         # Business logic
│   │   └── lead_service.py # ✅ Lead operations & scoring
│   └── main.py           # ✅ FastAPI application
├── requirements.txt      # ✅ Python dependencies
├── .env.example         # ✅ Environment template
└── docker-compose.yml   # ✅ Local development setup
```

## 🔑 Authentication (Temporary)

For MVP development, we're using a mock authentication system. 

**TODO**: Implement proper user registration and login endpoints.

## 📈 Lead Scoring Algorithm

Leads are automatically scored 0-100 based on:
- Has company name: +20 points
- Has job title: +15 points  
- Senior position keywords: +20 points
- Has phone number: +10 points
- Business email domain: +10 points
- Quality source (LinkedIn, referral): +10 points

## 🛣️ Next Steps

Now that you have the foundation working, let's add:

1. **User Authentication**: Real login/signup endpoints
2. **Campaign Management**: Create and manage email campaigns  
3. **AI Agent System**: Email generation with customization
4. **MCP Integration**: Connect to Gmail for sending emails
5. **Frontend**: React dashboard to manage leads and campaigns

## 🐛 Troubleshooting

**Database connection fails:**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check connection
docker-compose exec postgres psql -U postgres -d sales_automation -c "\dt"
```

**Import errors:**
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🤝 Development Tips

1. **Always use the service layer** for business logic
2. **Test endpoints** in the auto-generated docs at /docs
3. **Check logs** for debugging information
4. **Use type hints** everywhere for better code quality
5. **Keep endpoints thin** - delegate to services

Ready to add the next feature? Let me know what you'd like to build next!
