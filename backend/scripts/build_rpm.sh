#!/bin/bash

set -e

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

# Check if running on RHEL/CentOS
if [ ! -f /etc/redhat-release ]; then
    log_error "This script must be run on RHEL/CentOS"
    exit 1
fi

# Install build dependencies
log_info "Installing build dependencies..."
dnf install -y rpm-build rpmdevtools python39-devel postgresql-devel gcc

# Set up RPM build environment
log_info "Setting up RPM build environment..."
rpmdev-setuptree

# Create source tarball
log_info "Creating source tarball..."
VERSION="0.1.0"
NAME="password-vault"
TARBALL="${NAME}-${VERSION}.tar.gz"

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
mkdir -p "${TEMP_DIR}/${NAME}-${VERSION}"
cp -r ../* "${TEMP_DIR}/${NAME}-${VERSION}/"
cd "${TEMP_DIR}"
tar czf "$HOME/rpmbuild/SOURCES/${TARBALL}" "${NAME}-${VERSION}"

# Copy spec file
cp "../rpm/${NAME}.spec" "$HOME/rpmbuild/SPECS/"

# Build RPM
log_info "Building RPM..."
rpmbuild -ba "$HOME/rpmbuild/SPECS/${NAME}.spec"

# Clean up
rm -rf "${TEMP_DIR}"

log_info "RPM build complete!"
log_info "Your RPMs can be found in:"
log_info "  - $HOME/rpmbuild/RPMS/x86_64/"
log_info "  - $HOME/rpmbuild/SRPMS/"