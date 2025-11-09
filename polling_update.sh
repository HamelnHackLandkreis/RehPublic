#!/bin/bash

# Definieren Sie den Pfad zu Ihrem Update-Skript
# Da der Pfad bekannt ist, nutzen wir ihn direkt
PROJECT_DIR="/home/rehpublic/RehPublic"
UPDATE_SCRIPT="./smart_update.sh"
INTERVAL=60 # Wartezeit in Sekunden (60 Sekunden = 1 Minute)

echo "Starte automatischen Update-Dienst. Prüfung alle $INTERVAL Sekunden."

# Endlosschleife
while true; do
  echo "--- $(date) | Starte Update-Check ---"

  # Navigiere in das Projektverzeichnis und führe smart_update.sh mit sudo aus
  # sudo ist nötig für Docker, smart_update.sh handhabt die Git-Rechte intern
  sudo bash -c "cd $PROJECT_DIR && $UPDATE_SCRIPT"

  echo "--- Warte $INTERVAL Sekunden bis zum nächsten Check ---"
  sleep $INTERVAL
done
