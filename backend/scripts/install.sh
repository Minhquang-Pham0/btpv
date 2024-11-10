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

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run as root"
    exit 1
fi

# Generate secure random password
generate_password() {
    openssl rand -hex 16
}

# Path detection and setup
if [[ "$(basename $(pwd))" == "scripts" ]]; then
    BACKEND_DIR="$(dirname $(pwd))"
else
    BACKEND_DIR="$(pwd)"
fi

# Default values
INSTALL_DIR="/opt/password-vault"
CONFIG_DIR="/etc/password-vault"
LOG_DIR="/var/log/password-vault"
DATA_DIR="/var/lib/password-vault"
SERVICE_USER="password_vault"
SERVICE_GROUP="password_vault"
PYTHON_VENV="${INSTALL_DIR}/venv"
DB_NAME="password_vault"
DB_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)
ADMIN_PASSWORD=$(generate_password)

# Create required directories
create_directories() {
    log_info "Creating directory structure..."
    mkdir -p "${INSTALL_DIR}/app"
    mkdir -p "${CONFIG_DIR}"
    mkdir -p "${LOG_DIR}"
    mkdir -p "${DATA_DIR}"
    mkdir -p "${DATA_DIR}/db"
    mkdir -p "${INSTALL_DIR}/app/db/migrations/versions"
    mkdir -p "${CONFIG_DIR}/ssl"  # For SSL certificates
    mkdir -p "${CONFIG_DIR}/nginx"  # For NGINX configuration
}

# Create service user and group
create_service_user() {
    log_info "Creating service user and group..."
    if ! getent group "${SERVICE_GROUP}" >/dev/null; then
        groupadd -r "${SERVICE_GROUP}"
    fi
    if ! getent passwd "${SERVICE_USER}" >/dev/null; then
        useradd -r -g "${SERVICE_GROUP}" -d "${INSTALL_DIR}" -s /sbin/nologin "${SERVICE_USER}"
    fi
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."

    dnf config-manager --set-enabled codeready-builder-for-rhel-8-x86_64-rpms

    # Install EPEL
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
    dnf group install -y "Development Tools"
    
    # Python
    dnf module enable -y python39
    dnf install -y python39 python39-devel
    
    # PostgreSQL 13
    dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
    dnf -qy module disable postgresql
    dnf install -y postgresql13-server postgresql13-contrib postgresql13-devel
    dnf install -y postgresql-devel
    
    # NGINX and SSL
    dnf install -y nginx openssl mod_ssl certbot python3-certbot-nginx

    # Additional dependencies
    dnf install -y openssl-devel libffi-devel
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    sudo alternatives --set python3 /usr/bin/python3.9
    python3 -m venv "${PYTHON_VENV}"
    source "${PYTHON_VENV}/bin/activate"
    pip install --upgrade pip
    pip install -r "${BACKEND_DIR}/requirements.txt"
}

setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    # Generate strong DH parameters (this might take a few minutes)
    openssl dhparam -out "${CONFIG_DIR}/ssl/dhparam.pem" 2048

    # Generate self-signed certificate
    openssl req -x509 \
        -newkey rsa:4096 \
        -keyout "${CONFIG_DIR}/ssl/key.pem" \
        -out "${CONFIG_DIR}/ssl/cert.pem" \
        -days 365 \
        -nodes \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

    # Set proper permissions
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${CONFIG_DIR}/ssl/"*
    chmod 600 "${CONFIG_DIR}/ssl/key.pem"
    chmod 600 "${CONFIG_DIR}/ssl/dhparam.pem"
    chmod 644 "${CONFIG_DIR}/ssl/cert.pem"
}

# Configure NGINX
setup_nginx() {
    log_info "Configuring NGINX..."
    
    # Create NGINX configuration
    cat > /etc/nginx/conf.d/password-vault.conf << EOF
# Security headers
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    ''      close;
}

# HTTP -> HTTPS redirect for both main site and dev server
server {
    listen 80;
    server_name localhost;
    
    # Redirect all HTTP traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name localhost;

    # SSL configuration   
    ssl_certificate ${CONFIG_DIR}/ssl/cert.pem;
    ssl_certificate_key ${CONFIG_DIR}/ssl/key.pem;
    ssl_dhparam ${CONFIG_DIR}/ssl/dhparam.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;


    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        
        # WebSocket support
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        
        proxy_redirect off;
    }

    # API requests
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
    }
}
EOF

    # Test and enable NGINX configuration
    nginx -t
    systemctl enable nginx
    systemctl restart nginx
}

# Setup database
setup_database() {
    log_info "Setting up PostgreSQL..."
    
    # Initialize PostgreSQL 13 if not already initialized
    if [ ! -f /var/lib/pgsql/13/data/postgresql.conf ]; then
        /usr/pgsql-13/bin/postgresql-13-setup initdb
    fi

    # Configure pg_hba.conf for local connections
    cat > /var/lib/pgsql/13/data/pg_hba.conf << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all            postgres                                peer
local   all            all                                     md5
host    all            all             127.0.0.1/32            md5
host    all            all             ::1/128                 md5
EOF

    # Configure postgresql.conf
    cat > /var/lib/pgsql/13/data/postgresql.conf << EOF
listen_addresses = 'localhost'
port = 5432
max_connections = 100
shared_buffers = 128MB
dynamic_shared_memory_type = posix
max_wal_size = 1GB
min_wal_size = 80MB
log_timezone = 'UTC'
datestyle = 'iso, mdy'
timezone = 'UTC'
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'
EOF

    # Start and enable PostgreSQL
    systemctl enable postgresql-13
    systemctl start postgresql-13
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to start..."
    for i in {1..30}; do
        if su - postgres -c "/usr/pgsql-13/bin/psql -c '\l'" >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Create database and user
    log_info "Creating database and user..."
    sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS ${DB_NAME};
DROP USER IF EXISTS ${SERVICE_USER};
CREATE USER ${SERVICE_USER} WITH PASSWORD '${DB_PASSWORD}' CREATEDB;
CREATE DATABASE ${DB_NAME} OWNER ${SERVICE_USER};
\c ${DB_NAME}
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${SERVICE_USER};
EOF

    # Set ownership and permissions
    sudo -u postgres psql -d ${DB_NAME} << EOF
GRANT ALL ON SCHEMA public TO ${SERVICE_USER};
ALTER SCHEMA public OWNER TO ${SERVICE_USER};
EOF
}

# Create configuration files
create_config_files() {
    log_info "Creating configuration files..."
    
    # Create .env file
    cat > "${CONFIG_DIR}/.env" << EOF
# API Settings
PROJECT_NAME=Password Vault
API_V1_STR=/api/v1

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10

# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_USER=${SERVICE_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=${DB_NAME}

# CORS
BACKEND_CORS_ORIGINS=["https://localhost"]

# SSL Settings
SSL_CERT_PATH=${CONFIG_DIR}/ssl/cert.pem
SSL_KEY_PATH=${CONFIG_DIR}/ssl/key.pem
EOF

    # Create alembic.ini
    cat > "${INSTALL_DIR}/alembic.ini" << EOF
[alembic]
script_location = app/db/migrations
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
timezone = UTC
truncate_slug_length = 40
version_locations = %(here)s/app/db/migrations/versions
sqlalchemy.url = postgresql://${SERVICE_USER}:${DB_PASSWORD}@localhost/${DB_NAME}

[post_write_hooks]
[loggers]
keys = root,sqlalchemy,alembic
[handlers]
keys = console
[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

    # Copy application files
    cp -r "${BACKEND_DIR}/app"/* "${INSTALL_DIR}/app/"
}

# Initialize database schema
init_database() {
    log_info "Initializing database schema..."
    
    source "${PYTHON_VENV}/bin/activate"
    export PYTHONPATH="${INSTALL_DIR}"
    export POSTGRES_SERVER=localhost
    export POSTGRES_USER="${SERVICE_USER}"
    export POSTGRES_PASSWORD="${DB_PASSWORD}"
    export POSTGRES_DB="${DB_NAME}"
    
    cd "${INSTALL_DIR}"

    # Debug logging
    log_info "Current directory: $(pwd)"
    log_info "PYTHONPATH: ${PYTHONPATH}"
    log_info "Database URL: postgresql://${POSTGRES_USER}:****@${POSTGRES_SERVER}/${POSTGRES_DB}"
    
    # Verify database connection
    log_info "Verifying database connection..."
    if ! PGPASSWORD="${DB_PASSWORD}" psql -U "${SERVICE_USER}" -h localhost -d "${DB_NAME}" -c "\dx" > /dev/null 2>&1; then
        log_error "Failed to connect to database. Please check the credentials and database status."
        exit 1
    fi

    # Clear existing migration versions
    log_info "Clearing existing migrations..."
    rm -rf "app/db/migrations/versions"/*
    
    # Run database migrations with debug output
    log_info "Running database migrations..."
    ALEMBIC_DEBUG=1 alembic revision --autogenerate -m "initial"
    if [ $? -ne 0 ]; then
        log_error "Failed to create migration"
        exit 1
    fi
    
    ALEMBIC_DEBUG=1 alembic upgrade head
    if [ $? -ne 0 ]; then
        log_error "Failed to apply migration"
        exit 1
    fi

    # Verify the migrations
    log_info "Verifying migrations..."
    tables=$(PGPASSWORD="${DB_PASSWORD}" psql -U "${SERVICE_USER}" -h localhost -d "${DB_NAME}" -c "\dt" | grep -c 'users\|groups\|passwords\|group_members')
    if [ "$tables" -lt 4 ]; then
        log_error "Expected tables not found. Found $tables of 4 required tables."
        log_info "Current tables:"
        PGPASSWORD="${DB_PASSWORD}" psql -U "${SERVICE_USER}" -h localhost -d "${DB_NAME}" -c "\dt"
        exit 1
    else
        log_info "Successfully created $tables tables"
    fi
}

# # Create admin initialization script
create_admin_init_script() {
    log_info "Creating admin initialization script..."
    cat > "${INSTALL_DIR}/create_admin.py" << EOF
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.entities import User
from app.core.security import get_password_hash

def create_admin(db: Session):
    try:
        # Check if admin already exists
        if db.query(User).filter(User.username == "admin").first():
            print("Admin user already exists")
            return

        # Create new admin user with is_admin=True
        admin_user = User(
            username="admin",
            email="admin@saoc.snc",
            hashed_password=get_password_hash("${ADMIN_PASSWORD}"),
            is_active=True,
            is_admin=True  # Set admin privileges
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("Admin user created successfully")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {str(e)}")
        raise

def main():
    db = SessionLocal()
    try:
        create_admin(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
EOF

    chmod +x "${INSTALL_DIR}/create_admin.py"
}

# Initialize admin user
init_admin_user() {
    log_info "Initializing admin user..."
    
    # Ensure the virtual environment is activated
    source "${PYTHON_VENV}/bin/activate"
    
    # Set up environment variables
    export PYTHONPATH="${INSTALL_DIR}"
    export POSTGRES_SERVER=localhost
    export POSTGRES_USER="${SERVICE_USER}"
    export POSTGRES_PASSWORD="${DB_PASSWORD}"
    export POSTGRES_DB="${DB_NAME}"
    
    # Run the admin creation script
    cd "${INSTALL_DIR}"
    python create_admin.py
    
    # Check if the admin user was created successfully
    if PGPASSWORD="${DB_PASSWORD}" psql -U "${SERVICE_USER}" -h localhost -d "${DB_NAME}" -c "SELECT username FROM users WHERE username = 'admin';" | grep -q "admin"; then
        log_info "Admin user created successfully"
    else
        log_error "Failed to create admin user"
        exit 1
    fi

    # Save admin credentials securely
    cat > "${CONFIG_DIR}/admin_credentials.txt" << EOF
Admin Username: admin
Admin Email: admin@saoc.snc
Admin Password: ${ADMIN_PASSWORD}
EOF
    
    # Secure the credentials file
    chmod 600 "${CONFIG_DIR}/admin_credentials.txt"
    chown "${SERVICE_USER}:${SERVICE_GROUP}" "${CONFIG_DIR}/admin_credentials.txt"
    
    log_info "Admin credentials saved to: ${CONFIG_DIR}/admin_credentials.txt"
}

# Configure systemd service
setup_systemd() {
    log_info "Setting up systemd service..."
    cat > /etc/systemd/system/password-vault.service << EOF
[Unit]
Description=Password Vault Service
After=network.target postgresql-13.service nginx.service
Requires=postgresql-13.service nginx.service

[Service]
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${PYTHON_VENV}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
EnvironmentFile=${CONFIG_DIR}/.env
ExecStart=${PYTHON_VENV}/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable password-vault
}

# Set proper permissions
set_permissions() {
    log_info "Setting permissions..."
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}"
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${CONFIG_DIR}"
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${LOG_DIR}"
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${DATA_DIR}"
    
    chmod 750 "${INSTALL_DIR}"
    chmod 750 "${CONFIG_DIR}"
    chmod 750 "${LOG_DIR}"
    chmod 750 "${DATA_DIR}"
    chmod 600 "${CONFIG_DIR}/.env"
    chmod 600 "${INSTALL_DIR}/alembic.ini"
}

# Configure backup system and timer
setup_backup() {
    log_info "Setting up backup system..."
    
    # Create scripts directory and backup directory
    mkdir -p "${INSTALL_DIR}/scripts"
    mkdir -p "/var/backups/password-vault"
    
    # Install backup script
    cat > "${INSTALL_DIR}/scripts/backup.sh" << 'EOF'
#!/bin/bash
# scripts/backup.sh

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

# Default paths from installation
INSTALL_DIR="/opt/password-vault"
CONFIG_DIR="/etc/password-vault"
BACKUP_DIR="/var/backups/password-vault"
DB_NAME="password_vault"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE}.tar.gz"

# Ensure running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run as root"
    exit 1
fi

# Create backup function
create_backup() {
    log_info "Starting backup process..."

    # Create temporary directory for backup
    TEMP_DIR=$(mktemp -d)
    TEMP_BACKUP_DIR="${TEMP_DIR}/password-vault-backup"
    mkdir -p "${TEMP_BACKUP_DIR}"

    # Backup PostgreSQL database
    log_info "Backing up database..."
    sudo -u postgres pg_dump ${DB_NAME} > "${TEMP_BACKUP_DIR}/database.sql"

    # Backup configuration files
    log_info "Backing up configuration..."
    cp -r "${CONFIG_DIR}" "${TEMP_BACKUP_DIR}/config"

    # Backup SSL certificates
    log_info "Backing up SSL certificates..."
    cp -r "${CONFIG_DIR}/ssl" "${TEMP_BACKUP_DIR}/ssl"

    # Create compressed archive
    log_info "Creating backup archive..."
    tar -czf "${BACKUP_FILE}" -C "${TEMP_DIR}" .

    # Cleanup temporary files
    rm -rf "${TEMP_DIR}"

    # Set secure permissions
    chown root:root "${BACKUP_FILE}"
    chmod 600 "${BACKUP_FILE}"

    log_info "Backup completed successfully: ${BACKUP_FILE}"
}

# Rotate old backups function
rotate_backups() {
    # Keep last 7 daily backups
    log_info "Rotating old backups..."
    find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +7 -delete
}

# Main script logic
create_backup
rotate_backups

exit 0
EOF

    chmod +x "${INSTALL_DIR}/scripts/backup.sh"
    
    # Install systemd service and timer
    cat > "/etc/systemd/system/password-vault-backup.service" << EOF
[Unit]
Description=Password Vault Backup Service
After=postgresql-13.service

[Service]
Type=oneshot
ExecStart=${INSTALL_DIR}/scripts/backup.sh
User=root

[Install]
WantedBy=multi-user.target
EOF

    cat > "/etc/systemd/system/password-vault-backup.timer" << EOF
[Unit]
Description=Run Password Vault backup daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Reload systemd and enable timer
    systemctl daemon-reload
    systemctl enable password-vault-backup.timer
    systemctl start password-vault-backup.timer
    
    log_info "Backup system installed and scheduled"
}


# Add to the installation script
setup_frontend() {
    log_info "Setting up frontend..."
    
    # Install Node.js and npm (if not already in your dependencies)
    dnf install -y nodejs npm

    # Create frontend directory
    mkdir -p "${INSTALL_DIR}/frontend"
    
    # Copy frontend files
    cp -r "${BACKEND_DIR}/../frontend"/* "${INSTALL_DIR}/frontend/"
    
    # Install dependencies and build
    cd "${INSTALL_DIR}/frontend"
    npm install
    npm run build
    
    # Ensure proper permissions
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}/frontend"
}


# Main installation process
main() {
    log_info "Starting Password Vault installation..."
    
    create_directories
    create_service_user
    install_system_deps
    # setup_frontend
    setup_ssl              # New step for HTTPS
    setup_nginx           # New step for HTTPS
    install_python_deps
    setup_database
    create_config_files
    init_database
    create_admin_init_script
    init_admin_user
    setup_systemd
    set_permissions
    setup_backup  
    
    # Start services in correct order
    systemctl start postgresql-13
    systemctl start nginx
    systemctl start password-vault
    
    log_info "Installation completed successfully!"
    log_info "Service credentials saved to: ${CONFIG_DIR}/.env"
    log_info "Admin credentials saved to: ${CONFIG_DIR}/admin_credentials.txt"
    log_info "Access the application at: https://localhost"
    
    # Display the admin credentials
    log_info "Admin Credentials:"
    log_info "Username: admin"
    log_info "Password: ${ADMIN_PASSWORD}"
}

# Run main installation
main