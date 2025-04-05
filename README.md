# Thesis Management API

A Flask-based RESTful API for a thesis submission and advisor feedback system.

## Features

- User authentication and role-based access control
- Thesis submission and management
- Advisor feedback with inline comments
- PDF export for feedback reports
- Notifications for thesis status changes and feedback
- File upload and management
- Admin dashboard for system management

## Architecture

This project follows a Clean Architecture pattern with the following layers:

- **Domain Layer**: Core business entities and business rules
- **Application Layer**: Use cases, DTOs, and interfaces
- **Infrastructure Layer**: Database, external services, and repository implementations
- **API Layer**: HTTP routes, request/response handling, and middleware

## Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: MySQL (via XAMPP)
- **Authentication**: JWT
- **Storage**: Cloudinary
- **PDF Generation**: ReportLab, PyPDF2

## Project Structure

```
thesis_api/
├── domain/                # Domain layer
│   ├── entities/          # Core business entities
│   ├── exceptions/        # Domain-specific exceptions
│   └── value_objects/     # Immutable value objects
├── application/           # Application layer
│   ├── dtos/              # Data Transfer Objects
│   ├── interfaces/        # Repository and service interfaces
│   ├── use_cases/         # Business logic use cases
│   └── validators/        # Input validation
├── infrastructure/        # Infrastructure layer
│   ├── config/            # Application configuration
│   ├── database/          # Database models and connection
│   ├── repositories/      # Repository implementations
│   ├── services/          # External service implementations
│   └── migrations/        # Database migrations
├── api/                   # API layer
│   ├── middleware/        # Authentication and RBAC middleware
│   ├── routes/            # API endpoints
│   ├── schemas/           # Request/response validation schemas
│   └── error_handlers.py  # Centralized error handling
├── utils/                 # Utility functions
├── tests/                 # Tests
└── app.py                 # Application entry point
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- MySQL (XAMPP)
- Cloudinary account (for file storage)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd thesis-management-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables by copying `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Then update the variables in `.env` with your configuration.

### Database Setup

1. Start MySQL server through XAMPP.

2. Create a database:
   ```bash
   mysql -u root -p
   CREATE DATABASE thesis_management;
   EXIT;
   ```

3. Run database migrations:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

### Running the Application

Start the development server:
```bash
flask run
```

The API will be available at `http://localhost:5000`.

## API Documentation

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get access token
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (revoke token)
- `GET /api/auth/me` - Get current user profile

### Theses

- `POST /api/theses` - Create a new thesis
- `GET /api/theses` - Get list of theses
- `GET /api/theses/<thesis_id>` - Get thesis details
- `PUT /api/theses/<thesis_id>` - Update thesis
- `PUT /api/theses/<thesis_id>/status` - Update thesis status
- `GET /api/theses/<thesis_id>/download` - Download thesis file
- `POST /api/theses/<thesis_id>/assign` - Assign advisor to thesis

### Feedback

- `POST /api/feedback` - Provide feedback on a thesis
- `GET /api/feedback/thesis/<thesis_id>` - Get all feedback for a thesis
- `GET /api/feedback/<feedback_id>` - Get feedback details
- `PUT /api/feedback/<feedback_id>` - Update feedback
- `GET /api/feedback/<feedback_id>/export` - Export feedback as PDF

### Admin

- `GET /api/admin/users` - Get all users
- `PUT /api/admin/users/<user_id>` - Update user details
- `GET /api/admin/stats` - Get system statistics

## User Roles and Permissions

- **Student**: Can create and update theses, view feedback
- **Advisor**: Can review theses, provide feedback, approve/reject submissions
- **Admin**: Has access to all features, plus user management

## Testing

Run tests using pytest:
```bash
pytest
```

## Deployment

1. Configure production environment variables.
2. Use Gunicorn as a WSGI server:
   ```bash
   gunicorn "thesis_api.app:create_app()"
   ```
3. Set up a reverse proxy with Nginx.

## License

[MIT License](LICENSE)