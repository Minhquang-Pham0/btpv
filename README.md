# Baby Turtle Password Vault

A secure password management system with group sharing capabilities.

## Current Implementation

### Backend (FastAPI)
- ✅ Core configuration
- ✅ Database models (User, Group, Password)
- ✅ Authentication service with JWT
- ✅ Password encryption service
- ✅ Group management service
- ✅ Password management service
- ✅ API routes for all core functionality
- ✅ Basic error handling
- ✅ Database migrations setup
- ✅ RPM packaging structure

### Frontend (React)
- ✅ Authentication components
- ✅ Group management interface
- ✅ Password management interface
- ✅ API service integration
- ✅ Basic error handling
- ✅ Responsive design

## Installation

### Prerequisites
- RHEL 8/9
- Python 3.9+
- PostgreSQL 13+
- Node.js 18+ (for development)

### Quick Start
1. Install the RPM:
```bash
sudo dnf install password-vault-0.1.0-1.el8.x86_64.rpm
```

2. Start the service:
```bash
sudo systemctl start password-vault
```

3. Access the web interface:
```
http://your-server:8000
```

### Development Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd password-vault
```

2. Set up the backend:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env  # Edit with your settings
```

3. Set up the frontend:
```bash
cd frontend
npm install
cp .env.template .env  # Edit with your settings
```

4. Start the development servers:
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm start
```

## Prioritized Next Steps

### Critical (Security & Stability)
1. 🔴 Add TLS/HTTPS configuration
2. 🔴 Implement rate limiting for authentication
3. 🔴 Add password complexity requirements
4. 🔴 Set up proper logging
5. 🔴 Configure SELinux policies

### High Priority (Core Features)
1. 🟡 Add password generator - done
2. 🟡 Implement password visibility toggle - done
3. 🟡 Add copy to clipboard functionality - done
4. 🟡 Create backup/restore procedures
5. 🟡 Add password search functionality

### Medium Priority (Enhancement)
1. 🟢 Implement 2FA
2. 🟢 Add password history
3. 🟢 Create password categories/tags
4. 🟢 Add bulk import/export
5. 🟢 Implement password sharing

## API Documentation

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/test-token` - Validate token

### Groups
- `GET /api/v1/groups` - List user's groups
- `POST /api/v1/groups` - Create new group
- `PUT /api/v1/groups/{group_id}` - Update group
- `POST /api/v1/groups/{group_id}/members/{username}` - Add member

### Passwords
- `GET /api/v1/passwords/group/{group_id}` - List group passwords
- `POST /api/v1/passwords` - Create new password
- `PUT /api/v1/passwords/{password_id}` - Update password
- `DELETE /api/v1/passwords/{password_id}` - Delete password

## Security Considerations
- Passwords are encrypted at rest using Fernet encryption
- JWT-based authentication
- Group-based access control
- Database connection pooling
- Input validation on all endpoints

## Known Limitations
- No password history tracking
- Basic error handling
- Limited security hardening
- No automated backup system
- No high availability setup

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is proprietary and confidential.


## Project Structure
```
password-vault/
├── README.md
├── backend/
│   ├── requirements.txt*
│   ├── alembic.ini*
│   ├── .env*
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_groups.py
│   │   └── test_passwords.py
│   └── app/
│       ├── __init__.py
│       ├── main.py*
│       ├── api/
│       │   ├── __init__.py*
│       │   └── routes/
│       │       ├── __init__.py*
│       │       ├── auth.py*
│       │       ├── groups.py*
│       │       ├── passwords.py*
│       │       └── users.py*
│       ├── core/
│       │   ├── __init__.py*
│       │   ├── config.py*
│       │   ├── security.py*
│       │   └── exceptions.py*
│       ├── db/
│       │   ├── __init__.py*
│       │   ├── base.py*
│       │   ├── session.py*
│       │   └── migrations/
│       │       └── versions/
│       ├── models/
│       │   ├── __init__.py*
│       │   ├── entities/
│       │   │   ├── __init__.py*
│       │   │   ├── user.py*
│       │   │   ├── group.py*
│       │   │   └── password.py*
│       │   └── schemas/
│       │       ├── __init__.py*
│       │       ├── user.py*
│       │       ├── group.py*
│       │       ├── password.py*
│       │       └── token.py*
│       └── services/
│           ├── __init__.py*
│           ├── auth_service.py*
│           ├── group_service.py*
│           ├── password_service.py*
│           └── encryption_service.py*
├── frontend/
│   ├── package.json
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   └── src/
│       ├── index.js
│       ├── App.js
│       ├── components/
│       │   ├── auth/
│       │   │   ├── LoginForm.js
│       │   │   └── RegisterForm.js
│       │   ├── groups/
│       │   │   ├── GroupList.js
│       │   │   └── GroupForm.js
│       │   └── passwords/
│       │       ├── PasswordList.js
│       │       └── PasswordForm.js
│       ├── services/
│       │   ├── api.js*
│       │   ├── auth.js*
│       │   ├── groups.js*
│       │   └── passwords.js*
│       ├── hooks/
│       │   ├── useAuth.js
│       │   └── useApi.js
│       └── store/
│           ├── index.js
│           └── slices/
│               ├── authSlice.js
│               └── groupsSlice.js
└── deploy/
    ├── docker/
    │   ├── Dockerfile.backend
    │   ├── Dockerfile.frontend
    │   └── docker-compose.yml
    ├── nginx/
    │   └── nginx.conf
    └── scripts/
        ├── backup.sh
        └── deploy.sh
```




todo: 
user password complexity requirements.
password complexity requirements