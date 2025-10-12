#!/usr/bin/env bash
set -euo pipefail

#------------------------------------------------------------------------------
# Usage/help
#------------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $0 --env ENVIRONMENT [-p PORT] [-s] [-h]

Options:
  -e, --env ENV      one of: local, remote, dev, staging, production
  -p, --port PORT    override default PORT (env or fallback 8000)
  -s, --ssl          enable SSL (sets protocol to https)
  -h, --help         show this help and exit
EOF
  exit 1
}

#------------------------------------------------------------------------------
# Helper to update or append an env var in .env
#------------------------------------------------------------------------------
set_env_var() {
  local KEY="$1"
  local VAL="$2"
  if grep -qE "^${KEY}=" .env; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' -E "s|^${KEY}=.*|${KEY}=${VAL}|" .env
    else
      sed -i -E "s|^${KEY}=.*|${KEY}=${VAL}|" .env
    fi
  else
    echo "${KEY}=${VAL}" >> .env
  fi
}

#------------------------------------------------------------------------------
# Secret generation, OS detection, uv install, etc.
#------------------------------------------------------------------------------
generate_secret() { openssl rand -hex "${1:-32}"; }
prompt_generate_secrets() {
  read -r -p "Generate new secrets? [y/N] " ans
  case "$ans" in [Yy]*)
      echo "✔ Generating secrets…"
      SK=$(generate_secret 32); set_env_var SECRET_KEY "$SK"
      UP=$(generate_secret 16); set_env_var FIRST_SUPERUSER_PASSWORD "$UP"
      PP=$(generate_secret 16); set_env_var POSTGRES_PASSWORD "$PP";;
    *) echo "→ Skipping secret generation.";;
  esac
}
detect_os() {
  case "$(uname -s)" in
    Linux*) OS=linux;; Darwin*) OS=mac;; CYGWIN*|MINGW*|MSYS*) OS=windows;; *) OS=unknown;;
  esac
};
enable_uv() {
  command -v uv >/dev/null 2>&1 || {
    echo "uv not found; installing…"
    if [[ "$OS" == windows ]]; then
      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
      curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
  }
};
prompt_for_ssl() {
  if ! $USE_SSL; then
    read -r -p "Do you want to run server with SSL? [y/N] " ssl_ans
    case "$ssl_ans" in [Yy]*)
      USE_SSL=true
      echo "Using HTTPS for server host. Don't forget to put your custom certificates in certs directory" ;;
    *)
      USE_SSL=false;;
    esac
  fi
}

#------------------------------------------------------------------------------
# Defaults
#------------------------------------------------------------------------------
ENVIRONMENT="" PORT="${PORT:-8000}" USE_SSL=false

#------------------------------------------------------------------------------
# Parse options (compatible with macOS BSD getopt)
#------------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -p|--port)
      PORT="$2"
      shift 2
      ;;
    -s|--ssl)
      USE_SSL=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# Validate ENVIRONMENT
case "$ENVIRONMENT" in
  local|remote|dev|staging|production);;
  *) echo "Invalid environment: $ENVIRONMENT"; usage;;
esac

#------------------------------------------------------------------------------
# Copy .env.example → .env and set initial vars
#------------------------------------------------------------------------------

cp .env.example .env
prompt_generate_secrets
echo ""
prompt_for_ssl

PROTO=http
if $USE_SSL; then
  PROTO=https;
  mkdir -p certs
  set_env_var SSL_KEY_FILE "certs/ssl.key"
  set_env_var SSL_CERT_FILE "certs/ssl.crt"
fi

# Copy and inject
set_env_var ENVIRONMENT "$ENVIRONMENT"
set_env_var SERVER_PROTOCOL "$PROTO"
set_env_var SERVER_HOST "$HOST"
set_env_var SERVER_PORT "$PORT"
set_env_var CORS_ORIGINS "\"${PROTO}://$HOST:3000\""

detect_os
enable_uv

#------------------------------------------------------------------------------
# Run uv sync
#------------------------------------------------------------------------------
enable_uv
echo "Running uv sync…"
uv sync
#mkdir -p data/postgres
#mkdir -p data/userdata

#------------------------------------------------------------------------------
# Report (cross-platform with fallback)
#------------------------------------------------------------------------------

# Try to use tput if available, otherwise use no colors
if command -v tput >/dev/null 2>&1 && tput setaf 1 >/dev/null 2>&1; then
  bold=$(tput bold)
  green=$(tput setaf 2)
  blue=$(tput setaf 4)
  cyan=$(tput setaf 6)
  reset=$(tput sgr0)
else
  # Fallback to ANSI codes (works in Git Bash on Windows)
  bold="\033[1m"
  green="\033[32m"
  blue="\033[34m"
  cyan="\033[36m"
  reset="\033[0m"
fi

echo ""
printf "${bold}${green}========================================${reset}\n"
printf "${bold}${green}    Setup Finished Successfully!${reset}\n"
printf "${bold}${green}========================================${reset}\n"
echo ""

printf "${blue}${bold}%-20s${reset} ${cyan}%s${reset}\n" "Environment:" "$ENVIRONMENT"
printf "${blue}${bold}%-20s${reset} ${cyan}%s${reset}\n" "Host:" "$HOST"
printf "${blue}${bold}%-20s${reset} ${cyan}%s${reset}\n" "Port:" "$PORT"
printf "${blue}${bold}%-20s${reset} ${cyan}%s${reset}\n" "SSL Enabled:" "$USE_SSL"
printf "${blue}${bold}%-20s${reset} ${cyan}%s${reset}\n" "Protocol:" "$PROTO"
echo ""