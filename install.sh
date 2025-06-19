#!/bin/bash
# kotoba installer script
# Usage: curl -sSL https://raw.githubusercontent.com/0xkaz/kotoba/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check Python version
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.10 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.10"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python $PYTHON_VERSION is installed, but kotoba requires Python $REQUIRED_VERSION or higher."
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

# Check if pip is installed
check_pip() {
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip is not installed. Please install pip first."
        print_info "You can install pip with: python3 -m ensurepip --upgrade"
        exit 1
    fi
    print_success "pip is available"
}

# Install from PyPI
install_from_pypi() {
    print_info "Installing kotoba from PyPI..."
    
    # Create virtual environment (optional but recommended)
    if [ "$USE_VENV" = "true" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv kotoba-env
        source kotoba-env/bin/activate
        print_success "Virtual environment created and activated"
    fi
    
    # Install kotoba
    if python3 -m pip install --upgrade kotoba; then
        print_success "kotoba installed successfully!"
    else
        print_warning "PyPI installation failed. Installing from GitHub..."
        install_from_github
    fi
}

# Install from GitHub
install_from_github() {
    print_info "Installing kotoba from GitHub..."
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "git is not installed. Please install git first."
        exit 1
    fi
    
    # Clone repository
    INSTALL_DIR="${INSTALL_DIR:-$HOME/.kotoba}"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory $INSTALL_DIR already exists. Removing..."
        rm -rf "$INSTALL_DIR"
    fi
    
    print_info "Cloning repository to $INSTALL_DIR..."
    git clone https://github.com/0xkaz/kotoba.git "$INSTALL_DIR"
    
    cd "$INSTALL_DIR"
    
    # Install dependencies
    print_info "Installing dependencies..."
    python3 -m pip install -e .
    
    print_success "kotoba installed successfully from GitHub!"
}

# Check system requirements
check_system() {
    print_info "Checking system requirements..."
    
    # Check RAM
    if command -v free &> /dev/null; then
        TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
        if [ "$TOTAL_RAM" -lt 8000 ]; then
            print_warning "System has less than 8GB RAM. Consider using lightweight models or mock mode."
        fi
    fi
    
    # Check for playwright browsers
    print_info "Installing Playwright browsers..."
    python3 -m playwright install chromium
}

# Main installation function
main() {
    echo "======================================"
    echo "   kotoba Installation Script"
    echo "======================================"
    echo
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --venv)
                USE_VENV=true
                shift
                ;;
            --github)
                FORCE_GITHUB=true
                shift
                ;;
            --dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    check_python
    check_pip
    
    # Install kotoba
    if [ "$FORCE_GITHUB" = "true" ]; then
        install_from_github
    else
        install_from_pypi
    fi
    
    # Post-installation setup
    check_system
    
    # Print usage information
    echo
    print_success "Installation complete!"
    echo
    echo "To get started:"
    echo "  1. Run a test: kotoba --test-file tests/mock_test.yaml"
    echo "  2. Use mock mode: USE_MOCK_LLM=true kotoba --test-file tests/mock_test.yaml"
    echo "  3. View help: kotoba --help"
    echo
    echo "For more information, visit: https://github.com/0xkaz/kotoba"
    echo
}

# Run main function
main "$@"