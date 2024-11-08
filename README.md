# Baby Turtle Password Vault

A secure, multi-user password management system with group sharing capabilities and HTTPS encryption.

## Features

- **Secure Password Storage**: All passwords are encrypted at rest using Fernet encryption
- **Group-Based Access Control**: Share passwords securely within teams
- **HTTPS Support**: All communication is encrypted in transit
- **Multi-User Support**: Role-based access control with admin and regular users
- **Modern Web Interface**: Responsive design built with React and Tailwind CSS
- **API-First Design**: Built on FastAPI for robust API support
- **Database Backed**: PostgreSQL database for reliable data storage

## Security Features

- End-to-end HTTPS encryption
- Secure password hashing using bcrypt
- JWT-based authentication
- Strong security headers
- CORS protection
- XSS prevention
- CSRF protection
- Rate limiting
- Input validation and sanitization

## System Requirements

- RHEL 8/CentOS 8 or compatible
- Python 3.9+
- PostgreSQL 13
- Node.js 18+ (for development)
- Minimum 2GB RAM
- 10GB available disk space

## Quick Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/baby-turtle-password-vault.git
cd baby-turtle-password-vault
```

2. Run the installation script:
```bash
sudo ./install.sh
```

3. Access the web interface:
```
https://localhost
```

The installation script will:
- Set up all required dependencies
- Configure PostgreSQL database
- Generate SSL certificates
- Configure NGINX as a reverse proxy
- Create an admin user
- Start all required services

## Default Ports

- Web Interface: HTTPS/443
- API Backend: 8000 (internal)
- Database: 5432 (internal)

## Architecture

```
Frontend (React) → NGINX (HTTPS) → FastAPI Backend → PostgreSQL
```

### Components

- **Frontend**: React-based SPA with group and password management
- **NGINX**: Reverse proxy, SSL termination, and static file serving
- **Backend**: FastAPI application providing RESTful API
- **Database**: PostgreSQL storing encrypted passwords and user data

## API Documentation

The API documentation is available at:
```
https://your-server/api/v1/docs
```

Key endpoints:
- `/api/v1/auth/*`: Authentication endpoints
- `/api/v1/users/*`: User management
- `/api/v1/groups/*`: Group management
- `/api/v1/passwords/*`: Password management

## Development Setup

1. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set up the frontend:
```bash
cd frontend
npm install
```

3. Start development servers:
```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev
```

## Production Deployment

Additional steps for production:
1. Replace self-signed certificate with a valid SSL certificate
2. Update CORS settings with your domain
3. Configure proper firewall rules
4. Set up regular backups
5. Monitor system logs
6. Configure rate limiting

## Security Recommendations

1. Use strong passwords for admin accounts
2. Enable 2FA when available
3. Regularly update dependencies
4. Monitor access logs
5. Implement backup strategy
6. Use valid SSL certificates
7. Configure proper firewall rules

## Backup and Recovery

Automated backup script included:
```bash
./scripts/backup.sh
```

This will backup:
- Database contents
- Configuration files
- SSL certificates
- User data


## License

Proprietary - All rights reserved

## Support

For support:
- Create an issue in the repository
- Contact system administrator
- Check documentation in `/docs`

## Acknowledgments

Built with:
- FastAPI
- React
- PostgreSQL
- NGINX
- Tailwind CSS
- SQLAlchemy

## Version History

- 1.0.0: Initial release with HTTPS support
- 0.9.0: Beta release with basic functionality
- 0.8.0: Alpha release for testing

---

Remember to replace the default admin password after installation and maintain regular security updates.

For more information, see the detailed documentation in the `/docs` directory.