# Project Structure
src/
├── core/
│   ├── __init__.py
│   ├── .env
│   ├── config.py
├── models/
│   ├── __init__.py
│   ├── [model-name].py
├── services/
│   ├── __init__.py
│   ├── [x_service].py
├── api/
│   ├── __init__.py
│   ├── [x_routes].py
├── repositories/
│   ├── __init__.py
│   └── base_repository.py
│   └── [x_repository].py
├── utils/
│   ├── __init__.py
│   └── [x_utils].py
├── app.py