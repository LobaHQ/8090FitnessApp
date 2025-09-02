# 8090 Fitness App

A fitness application backend with user authentication via AWS Cognito and user profile management.

## Features

- User registration and authentication via AWS Cognito
- JWT token-based authentication
- User profile management
- RESTful API built with FastAPI

## Project Structure

```
8090FitnessApp/
├── src/
│   ├── api/
│   │   └── auth.py          # Authentication endpoints
│   ├── services/
│   │   └── cognito_service.py  # AWS Cognito integration
│   ├── database/
│   │   └── user_repository.py  # Database operations
│   └── models/
│       └── auth_models.py      # Pydantic models
├── main.py                      # FastAPI application
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment variables template
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/LobaHQ/8090FitnessApp.git
cd 8090FitnessApp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your AWS Cognito and database credentials
```

5. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and receive JWT tokens
- `POST /api/auth/refresh-token` - Refresh JWT tokens

## API Documentation

Once the application is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## Environment Variables

- `AWS_REGION` - AWS region for Cognito
- `COGNITO_USER_POOL_ID` - Cognito User Pool ID
- `COGNITO_CLIENT_ID` - Cognito App Client ID
- `COGNITO_CLIENT_SECRET` - Cognito App Client Secret (optional)
- `DATABASE_URL` - Database connection string
- `PORT` - Application port (default: 8000)
- `ENV` - Environment (development/production)
- `ALLOWED_ORIGINS` - CORS allowed origins

## Development

To run in development mode with auto-reload:
```bash
uvicorn main:app --reload --port 8000
```

## Testing

```bash
pytest
```

## License

MIT