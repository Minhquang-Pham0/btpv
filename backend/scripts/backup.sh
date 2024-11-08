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

    # Create backup directory if it doesn't exist
    mkdir -p "${BACKUP_DIR}"

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

    # Backup NGINX configuration
    log_info "Backing up NGINX configuration..."
    cp /etc/nginx/conf.d/password-vault.conf "${TEMP_BACKUP_DIR}/nginx.conf"

    # Backup version information and metadata
    log_info "Saving metadata..."
    cat > "${TEMP_BACKUP_DIR}/metadata.txt" << EOF
Backup Date: $(date)
Version: 1.0.0
PostgreSQL Version: $(postgres --version)
NGINX Version: $(nginx -v 2>&1)
Python Version: $(python3 --version)
EOF

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

# Restore from backup function
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    }

    log_info "Starting restore process from: $backup_file"
    
    # Create temporary directory for restoration
    TEMP_DIR=$(mktemp -d)

    # Extract backup archive
    tar -xzf "$backup_file" -C "${TEMP_DIR}"
    
    # Stop services
    log_info "Stopping services..."
    systemctl stop password-vault nginx

    # Restore database
    log_info "Restoring database..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};"
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};"
    sudo -u postgres psql ${DB_NAME} < "${TEMP_DIR}/password-vault-backup/database.sql"

    # Restore configuration files
    log_info "Restoring configuration..."
    cp -r "${TEMP_DIR}/password-vault-backup/config"/* "${CONFIG_DIR}/"

    # Restore SSL certificates
    log_info "Restoring SSL certificates..."
    cp -r "${TEMP_DIR}/password-vault-backup/ssl"/* "${CONFIG_DIR}/ssl/"

    # Restore NGINX configuration
    log_info "Restoring NGINX configuration..."
    cp "${TEMP_DIR}/password-vault-backup/nginx.conf" /etc/nginx/conf.d/password-vault.conf

    # Set proper permissions
    log_info "Setting permissions..."
    chown -R password_vault:password_vault "${CONFIG_DIR}"
    chmod 600 "${CONFIG_DIR}/ssl/key.pem"
    chmod 600 "${CONFIG_DIR}/ssl/dhparam.pem"
    chmod 644 "${CONFIG_DIR}/ssl/cert.pem"

    # Cleanup temporary files
    rm -rf "${TEMP_DIR}"

    # Start services
    log_info "Starting services..."
    systemctl start nginx password-vault

    log_info "Restore completed successfully"
}

# Rotate old backups function
rotate_backups() {
    # Keep last 7 daily backups
    log_info "Rotating old backups..."
    find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +7 -delete
}

# List available backups function
list_backups() {
    log_info "Available backups:"
    ls -lh "${BACKUP_DIR}"/*.tar.gz 2>/dev/null || echo "No backups found"
}

# Main script logic
case "$1" in
    backup)
        create_backup
        rotate_backups
        ;;
    restore)
        if [ -z "$2" ]; then
            log_error "Please specify backup file to restore"
            echo "Usage: $0 restore <backup_file>"
            exit 1
        fi
        restore_backup "$2"
        ;;
    list)
        list_backups
        ;;
    *)
        echo "Usage: $0 {backup|restore <backup_file>|list}"
        echo "Examples:"
        echo "  $0 backup          # Create new backup"
        echo "  $0 list           # List available backups"
        echo "  $0 restore /path/to/backup_20240108_120000.tar.gz  # Restore from backup"
        exit 1
        ;;
esac

exit 0