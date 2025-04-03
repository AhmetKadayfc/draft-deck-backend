# Project Structure
src/
├── core/
│   ├── __init__.py
│   ├── .env
│   └── config.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── role.py
│   ├── student.py
│   ├── advisor.py
│   ├── thesis.py
│   ├── feedback.py
│   └── notifications.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── thesis_service.py
│   ├── feedback_service.py
│   └── notification_service.py
├── api/
│   ├── __init__.py
│   ├── auth_routes.py
│   ├── user_routes.py
│   ├── thesis_routes.py
│   ├── feebback_routes.py
│   └── notification_routes.py
├── repositories/
│   ├── __init__.py
│   ├── base_repository.py
│   ├── auth_repository.py
│   ├── user_repository.py
│   ├── thesis_repository.py
│   ├── feedback_repository.py
│   └── notification_repository.py
├── utils/
│   ├── __init__.py
│   ├── auth_utils.py.py
│   └── rbac_utils.py.py
├── migrations/
├── tests/
└── app.py


