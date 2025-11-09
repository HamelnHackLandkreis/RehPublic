#!/bin/bash

# Pfad zu Ihrem Repository, der die docker-compose.yml enthält
REPO_PATH="/home/rehpublic/RehPublic"
PROJECT_NAME="hackathon-rehpublic"

echo "Starte Deployment-Skript..."

# 1. Wechsel in das Projektverzeichnis
cd $REPO_PATH || { echo "Fehler: Verzeichnis $REPO_PATH nicht gefunden"; exit 1; }

# 2. Ziehe die neuesten Änderungen aus dem Git-Repository
echo "Pulle neueste Daten..."
git pull origin main

# 3. Baue die neuen Container (stellt sicher, dass die Images aktualisiert werden)
# --no-deps: Baut nur die geänderten Services
# --force-recreate: Erzwingt die Neuerstellung der Container
# --build: Baut die Images neu
echo "Baue und starte Docker Compose neu..."
docker compose up -d --build --force-recreate
#docker compose up -d

# 4. Bereinigen alter, ungenutzter Images, um Speicher freizugeben
echo "Bereinige alte Images..."
docker image prune -f

echo "Deployment abgeschlossen!"
