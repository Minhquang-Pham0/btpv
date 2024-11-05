from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.services.auth_service import AuthService
from app.models.schemas import UserCreate
from app.models.entities import User

def create_admin_user(
    db: Session,
    username: str,
    email: str,
    password: str
) -> None:
    """Create admin user if it doesn't exist"""
    # Check if admin user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"Admin user '{username}' already exists")
        return existing_user

    try:
        auth_service = AuthService(db)
        user_data = UserCreate(
            username=username,
            email=email,
            password=password
        )
        user = auth_service.create_user(user_data)
        print(f"Admin user '{username}' created successfully")
        return user
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        raise

if __name__ == "__main__":
    db = SessionLocal()
    try:
        create_admin_user(
            db,
            username="admin",
            email="admin@example.com",
            password="adminpassword123"
        )
    finally:
        db.close()
        
        
        
        
        #!/bin/bash

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate secure random password
generate_password() {
    openssl rand -base64 16
}

# Default values
INSTALL_DIR="/opt/password-vault"
CONFIG_DIR="/etc/password-vault"
LOG_DIR="/var/log/password-vault"
DATA_DIR="/var/lib/password-vault"
SERVICE_USER="password_vault"
SERVICE_GROUP="password_vault"
PYTHON_VENV="${INSTALL_DIR}/venv"
DB_NAME="password_vault"

# Generate secure passwords
DB_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)
ADMIN_PASSWORD=$(generate_password)  # Generate admin password

# Create admin user initialization script
create_admin_init_script() {
    log_info "Creating admin initialization script..."
    cat > "${INSTALL_DIR}/create_admin.py" << EOF
from app.db.session import SessionLocal
from app.services.auth_service import AuthService
from app.models.schemas import UserCreate

def create_admin():
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        user_data = UserCreate(
            username="admin",
            email="admin@${DOMAIN:-localhost}",
            password="${ADMIN_PASSWORD}"
        )
        auth_service.create_user(user_data)
        print("Admin user created successfully")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
EOF

    # Make the script executable
    chmod +x "${INSTALL_DIR}/create_admin.py"
}

# Initialize admin user
init_admin_user() {
    log_info "Initializing admin user..."
    source "${PYTHON_VENV}/bin/activate"
    export PYTHONPATH="${INSTALL_DIR}"
    python "${INSTALL_DIR}/create_admin.py"

    # Save admin credentials securely
    cat > "${CONFIG_DIR}/admin_credentials.txt" << EOF
Admin Username: admin
Admin Email: admin@${DOMAIN:-localhost}
Admin Password: ${ADMIN_PASSWORD}
EOF
    
    # Secure the credentials file
    chmod 600 "${CONFIG_DIR}/admin_credentials.txt"
    chown "${SERVICE_USER}:${SERVICE_GROUP}" "${CONFIG_DIR}/admin_credentials.txt"
}

# Main installation process
main() {
    log_info "Starting Password Vault installation..."
    
    create_directories
    create_service_user
    create_env_file
    install_system_deps
    install_python_deps
    setup_database
    create_admin_init_script
    setup_systemd
    init_database
    init_admin_user
    set_permissions
    
    log_info "Installation completed successfully!"
    log_info "Your database credentials have been saved to: ${CONFIG_DIR}/.env"
    log_info "Admin credentials have been saved to: ${CONFIG_DIR}/admin_credentials.txt"
    log_info "You can start the service with: systemctl start password-vault"
    
    # Display admin credentials
    log_info "Admin Credentials:"
    log_info "Username: admin"
    log_info "Password: ${ADMIN_PASSWORD}"
    log_info "Email: admin@${DOMAIN:-localhost}"
    log_info ""
    log_warn "Please save these credentials securely and change the password on first login!"
}

# Run main installation
main
