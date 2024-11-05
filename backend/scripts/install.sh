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

# Create required directories
create_directories() {
    log_info "Creating directory structure..."
    mkdir -p "${INSTALL_DIR}/app"
    mkdir -p "${CONFIG_DIR}"
    mkdir -p "${LOG_DIR}"
    mkdir -p "${DATA_DIR}"
    mkdir -p "${DATA_DIR}/db"
    mkdir -p "${INSTALL_DIR}/app/db/migrations/versions"
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
    
    # Enable CodeReady repository for additional packages
    subscription-manager repos --enable codeready-builder-for-rhel-9-$(arch)-rpms || true
    
    # Enable EPEL
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm || true
    
    # Install development tools and dependencies
    dnf group install -y "Development Tools"
    dnf install -y python3-devel python3-pip postgresql-server postgresql-contrib postgresql-devel gcc openssl-devel libffi-devel
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    python3 -m venv "${PYTHON_VENV}"
    source "${PYTHON_VENV}/bin/activate"
    pip install --upgrade pip
    pip install -r "${BACKEND_DIR}/requirements.txt"
}
setup_database() {
    log_info "Setting up PostgreSQL..."
    
    # Initialize PostgreSQL if not already initialized
    if [ ! -f /var/lib/pgsql/data/postgresql.conf ]; then
        postgresql-setup --initdb
    fi

    # Configure pg_hba.conf for local connections
    cat > /var/lib/pgsql/data/pg_hba.conf << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all            postgres                                peer
local   all            all                                     md5
host    all            all             127.0.0.1/32            md5
host    all            all             ::1/128                 md5
EOF

    # Configure postgresql.conf
    cat > /var/lib/pgsql/data/postgresql.conf << EOF
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

    # Restart PostgreSQL to apply configuration
    systemctl restart postgresql
    systemctl enable postgresql
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to start..."
    for i in {1..30}; do
        if sudo -u postgres psql -c '\l' >/dev/null 2>&1; then
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
ACCESS_TOKEN_EXPIRE_MINUTES=30

# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_USER=${SERVICE_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=${DB_NAME}

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
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
init_database() {
    log_info "Initializing database schema..."
    
    # Create app directory in install location
    mkdir -p "${INSTALL_DIR}/app"
    mkdir -p "${INSTALL_DIR}/app/db/migrations/versions"
    
    # Copy application files
    log_info "Copying application files..."
    cp -r "${BACKEND_DIR}/app"/* "${INSTALL_DIR}/app/"
    
    # Set up environment for alembic
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
# Configure systemd service
setup_systemd() {
    log_info "Setting up systemd service..."
    cat > /etc/systemd/system/password-vault.service << EOF
[Unit]
Description=Password Vault Service
After=network.target postgresql.service

[Service]
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${PYTHON_VENV}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
EnvironmentFile=${CONFIG_DIR}/.env
ExecStart=${PYTHON_VENV}/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
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

# Main installation process
main() {
    log_info "Starting Password Vault installation..."
    
    create_directories
    create_service_user
    install_system_deps
    install_python_deps
    setup_database
    create_config_files
    init_database
    setup_systemd
    set_permissions
    
    log_info "Installation completed successfully!"
    log_info "Credentials have been saved to: ${CONFIG_DIR}/.env"
    log_info "Start the service with: systemctl start password-vault"
}

# Run main installation
main