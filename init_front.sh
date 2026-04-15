#!/bin/sh

#on sort à la première erreur
set -e

#importer le mot de passe admin qui est dans .env, syntaxe BASIC_AUTH_PASSWORD=xxx
. ./.env

CERT_DIR="deployments/nginx/certs"
HTPASSWD_FILE="deployments/nginx/.htpasswd"
USER="admin"

mkdir -p "$CERT_DIR"
mkdir -p "$(dirname "$HTPASSWD_FILE")"

# Génération certificat + clé auto-signés
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$CERT_DIR/nginx.key" -out "$CERT_DIR/nginx.crt" -subj "/CN=localhost"

printf "%s" "$BASIC_AUTH_PASSWORD" | htpasswd -ciB "$HTPASSWD_FILE" "$USER"

chmod 640 "$HTPASSWD_FILE"

