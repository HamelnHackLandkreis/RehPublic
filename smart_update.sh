#!/bin/bash

# Dieses Skript ist so konzipiert, dass es MIT 'sudo' ausgeführt wird,
# um die notwendigen Rechte für Docker zu erhalten.
# Der 'git pull' Teil wird explizit als der ursprüngliche Benutzer ausgeführt,
# um auf dessen SSH-Schlüssel zugreifen zu können.

# Prüfe, ob das Skript mit sudo aufgerufen wurde
if [ "$EUID" -ne 0 ]; then
  echo "⚠️ Dieses Skript sollte mit 'sudo' aufgerufen werden, um die Rechte für Docker zu erhalten."
  echo "Bitte starte es mit: sudo ./smart_update.sh"
  exit 1
fi

# Setze den Benutzer, der das Skript aufgerufen hat (für Git-Berechtigungen)
TARGET_USER=$SUDO_USER
PROJECT_DIR=$(pwd)

# --- 1. Git Pull und Status prüfen ---

echo "▶️ Führe Git Pull als Benutzer $TARGET_USER aus und prüfe auf Änderungen..."

# Führe 'git pull' explizit als der ursprüngliche Benutzer aus und navigiere vorher ins Projektverzeichnis
GIT_OUTPUT=$(sudo -u $TARGET_USER bash -c "cd $PROJECT_DIR && git pull" 2>&1)
GIT_EXIT_CODE=$?

# Prüfe den Exit Code von Git
if [ $GIT_EXIT_CODE -ne 0 ]; then
    echo "❌ Git Pull ist fehlgeschlagen (Fehlercode $GIT_EXIT_CODE). Beende Skript."
    echo "Ausgabe:"
    echo "$GIT_OUTPUT"
    # Wenn ein Permission Denied auftritt, ist es wahrscheinlich ein SSH-Schlüssel Problem
    if echo "$GIT_OUTPUT" | grep -q "Permission denied (publickey)"; then
        echo "💡 HINWEIS: Prüfe, ob dein SSH-Schlüssel im Schlüsselbund des Benutzers $TARGET_USER geladen ist."
    fi
    exit 1
fi

# Prüfe die Ausgabe, ob das Repository bereits aktuell ist
if echo "$GIT_OUTPUT" | grep -q "Already up to date." || echo "$GIT_OUTPUT" | grep -q "schon aktuell."; then
    echo "ℹ️ Repository ist bereits aktuell. Docker-Container werden NICHT neu gestartet."
    exit 0
fi

echo "✅ Neue Änderungen gefunden. Starte Deployment-Prozess."

# --- 2. Docker-Befehle ausführen (als Root) ---

echo "▶️ Stoppe und entferne aktuelle Container (docker compose down)..."
# Führe Docker-Befehle als Root aus
docker compose down
if [ $? -ne 0 ]; then
    echo "❌ Fehler bei 'docker compose down'. Weiter mit 'up' versuchen."
fi
echo "✅ Container gestoppt und entfernt."

echo "▶️ Baue Images neu und starte Container im Hintergrund (docker compose up --build -d)..."
docker compose up --build -d
if [ $? -ne 0 ]; then
    echo "❌ Docker Compose Up ist fehlgeschlagen. Überprüfe die Logs."
    exit 1
fi

echo "🎉 Deployment abgeschlossen! Container laufen mit den neuen Änderungen."
