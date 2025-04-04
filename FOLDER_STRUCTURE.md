# Project Structure

src/
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── thesis.py
│   │   ├── feedback.py
│   │   └── notification.py
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── domain_exceptions.py
│   └── value_objects/
│       ├── __init__.py
│       └── status.py
├── application/
│   ├── __init__.py
│   ├── dtos/
│   │   ├── __init__.py
│   │   ├── user_dto.py
│   │   ├── thesis_dto.py
│   │   └── feedback_dto.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── thesis_repository.py
│   │   │   └── feedback_repository.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py
│   │       ├── storage_service.py
│   │       └── notification_service.py
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── login_use_case.py
│   │   │   └── register_use_case.py
│   │   ├── thesis/
│   │   │   ├── __init__.py
│   │   │   ├── submit_thesis_use_case.py
│   │   │   └── get_thesis_use_case.py
│   │   └── feedback/
│   │       ├── __init__.py
│   │       ├── provide_feedback_use_case.py
│   │       └── export_feedback_use_case.py
│   └── validators/
│       ├── __init__.py
│       └── input_validators.py
├── infrastructure/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user_model.py
│   │   │   ├── thesis_model.py
│   │   │   └── feedback_model.py
│   │   └── connection.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository_impl.py
│   │   ├── thesis_repository_impl.py
│   │   └── feedback_repository_impl.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── jwt_service.py
│   │   ├── cloudinary_service.py
│   │   ├── pdf_service.py
│   │   └── email_service.py
│   └── migrations/
│       ├── __init__.py
│       └── versions/
├── api/
│   ├── __init__.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   └── rbac_middleware.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── thesis_routes.py
│   │   ├── feedback_routes.py
│   │   └── admin_routes.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── request/
│   │   │   ├── __init__.py
│   │   │   ├── auth_schemas.py
│   │   │   ├── thesis_schemas.py
│   │   │   └── feedback_schemas.py
│   │   └── response/
│   │       ├── __init__.py
│   │       ├── auth_schemas.py
│   │       ├── thesis_schemas.py
│   │       └── feedback_schemas.py
│   └── error_handlers.py
├── utils/
│   ├── __init__.py
│   ├── auth_utils.py
│   ├── rbac_utils.py
│   └── file_utils.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   └── integration/
│       ├── __init__.py
│       └── api/
└── app.py