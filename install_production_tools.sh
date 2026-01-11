#!/bin/bash
# Install all critical production engineering tools
# For master engineers working on real production projects

set -e

echo "==========================================="
echo "🚀 PRODUCTION TOOLS INSTALLER"
echo "==========================================="
echo ""

if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew required"
    exit 1
fi

install_tool() {
    local tool=$1
    local formula=${2:-$tool}
    local check_cmd=${3:-"$tool --version"}
    
    if command -v "$tool" &> /dev/null; then
        echo "  ✅ $tool: Already installed"
        return 0
    fi
    
    echo "  ❌ $tool: Installing..."
    if brew install "$formula" > /dev/null 2>&1; then
        if command -v "$tool" &> /dev/null; then
            echo "  ✅ $tool: Installed successfully"
            return 0
        fi
    fi
    
    echo "  ⚠️  $tool: Installation failed or not available"
    return 1
}

# Security Scanning Tools
echo "🔒 Installing Security Scanning Tools..."
install_tool "snyk" "snyk"
install_tool "trivy" "trivy"
install_tool "semgrep" "semgrep"
echo ""

# Performance Profiling Tools
echo "⚡ Installing Performance Profiling Tools..."
install_tool "py-spy" "py-spy"
# cProfile is part of Python standard library
echo "  ✅ cProfile: Available (Python stdlib)"
echo ""

# Load Testing Tools
echo "📊 Installing Load Testing Tools..."
install_tool "k6" "k6"
install_tool "wrk" "wrk"
# ab (Apache Bench) is usually pre-installed
if command -v ab &> /dev/null; then
    echo "  ✅ ab: Already installed"
else
    echo "  ⚠️  ab: Not found (usually pre-installed)"
fi
install_tool "locust" "locust"
echo ""

# Container Orchestration Tools
echo "☸️  Installing Container Orchestration Tools..."
install_tool "kubectl" "kubectl"
install_tool "helm" "helm"
install_tool "docker-compose" "docker-compose"
# k9s is optional
install_tool "k9s" "k9s" || echo "  ⚠️  k9s: Optional, installation skipped"
echo ""

# Database Migration Tools
echo "🗄️  Installing Database Migration Tools..."
# Alembic is a Python package
if command -v pip3 &> /dev/null; then
    echo "  Installing alembic via pip..."
    pip3 install --user alembic > /dev/null 2>&1 && echo "  ✅ alembic: Installed" || echo "  ⚠️  alembic: Install manually with 'pip3 install alembic'"
else
    echo "  ⚠️  alembic: pip3 not found"
fi
install_tool "flyway" "flyway" || echo "  ⚠️  flyway: May need manual installation"
install_tool "dbmate" "dbmate"
echo ""

# Monitoring/Observability Tools
echo "📈 Installing Monitoring/Observability Tools..."
install_tool "prometheus" "prometheus" || echo "  ⚠️  prometheus: May need manual installation or use via Docker"
# Grafana CLI
install_tool "grafana" "grafana" || echo "  ⚠️  grafana: Usually runs as service, CLI optional"
echo ""

# Secrets Management Tools
echo "🔐 Installing Secrets Management Tools..."
install_tool "vault" "vault"
install_tool "sops" "sops"
echo ""

# Additional Production Tools
echo "🛠️  Installing Additional Production Tools..."
# Memory profiler
if command -v pip3 &> /dev/null; then
    pip3 install --user memory-profiler line-profiler > /dev/null 2>&1 && echo "  ✅ memory-profiler, line-profiler: Installed" || echo "  ⚠️  memory-profiler: Install manually"
fi
echo ""

echo "==========================================="
echo "✅ PRODUCTION TOOLS INSTALLATION COMPLETE"
echo "==========================================="
echo ""
echo "📋 Summary:"
echo "  • Security: snyk, trivy, semgrep"
echo "  • Profiling: py-spy, cProfile"
echo "  • Load Testing: k6, wrk, locust"
echo "  • Orchestration: kubectl, helm, docker-compose"
echo "  • Migrations: alembic (pip), dbmate"
echo "  • Monitoring: prometheus, grafana"
echo "  • Secrets: vault, sops"
echo ""
echo "Note: Some tools may require additional configuration"
echo ""
