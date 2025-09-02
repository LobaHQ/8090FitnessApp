# 8090 Fitness App - Full Stack Implementation

A comprehensive fitness application with AI-powered workout generation, built with modern cloud-native architecture.

## Architecture Overview

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: SQLModel ORM with PostgreSQL (Aurora-compatible)
- **Authentication**: AWS Cognito integration
- **API Structure**: RESTful endpoints organized by domain
- **Security**: JWT tokens, CORS configuration, secure password hashing

### Frontend (React + Vite)
- **Build Tool**: Vite for fast development
- **UI Framework**: shadcn/ui components with Tailwind CSS
- **State Management**: React Context + hooks
- **Authentication**: AWS Amplify with Cognito
- **Routing**: React Router v6
- **API Integration**: Custom useApi hook with Axios

### Database Architecture
- **ORM**: SQLModel (Pydantic + SQLAlchemy)
- **Migrations**: Alembic for schema versioning
- **Models**: User, UserProfile, WorkoutProgram, Exercise, etc.

## Project Structure

```
8090FitnessApp/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # API endpoints
│   │   ├── core/          # Core configuration
│   │   ├── database/      # Database session
│   │   ├── models/        # SQLModel definitions
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   └── alembic/           # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # Context providers
│   │   ├── hooks/         # Custom hooks
│   │   ├── pages/         # Page components
│   │   └── services/      # API services
│   └── public/
└── docs/                  # Documentation

```

## Features Implemented

### Authentication & User Management
- ✅ User registration with email/password
- ✅ Google OAuth integration
- ✅ JWT token-based authentication
- ✅ Profile management endpoints
- ✅ Onboarding flow

### Backend APIs
- ✅ `/api/v1/auth/*` - Authentication endpoints
- ✅ `/api/v1/profile` - User profile management
- ✅ `/api/v1/onboarding` - Onboarding completion
- 🔄 `/api/v1/workout-programs/*` - Workout generation (in progress)

### Frontend Features
- ✅ React app with Vite setup
- ✅ AWS Amplify configuration
- ✅ Authentication context
- ✅ Protected routes
- ✅ Custom API hook with auth
- 🔄 UI components (in progress)

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- AWS Account with Cognito User Pool

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Cognito configuration
```

4. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Environment Variables

### Backend (.env)
```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=fitness_app

# AWS Cognito
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=your_pool_id
COGNITO_CLIENT_ID=your_client_id
COGNITO_CLIENT_SECRET=your_client_secret

# Application
SECRET_KEY=your_secret_key
ENVIRONMENT=development
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_COGNITO_USER_POOL_ID=your_pool_id
VITE_COGNITO_CLIENT_ID=your_client_id
VITE_COGNITO_IDENTITY_POOL_ID=your_identity_pool_id
VITE_COGNITO_DOMAIN=your_cognito_domain
```

## API Documentation

Once the backend is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

### Backend Deployment (AWS ECS/Fargate)
1. Build Docker image
2. Push to ECR
3. Deploy to ECS with Fargate

### Frontend Deployment (AWS S3 + CloudFront)
1. Build production bundle: `npm run build`
2. Upload to S3
3. Configure CloudFront distribution

## Next Steps

- [ ] Complete AI service integration
- [ ] Implement workout program generation
- [ ] Add exercise swap functionality
- [ ] Create nutrition planning service
- [ ] Implement recovery & wellness features
- [ ] Add real-time progress tracking
- [ ] Set up monitoring and analytics

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.