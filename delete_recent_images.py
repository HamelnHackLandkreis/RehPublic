#!/usr/bin/env python3
import psycopg2
import sys
from datetime import datetime, timedelta

# ---------- CONFIG ----------
DB_CONFIG = {
    "host": "135.181.78.114",
    "port": 5432,
    "dbname": "rehpublic",
    "user": "rehpublic",
    "password": "hamelnhack2025",
}
# ----------------------------


def delete_recent_images(hours: int = 48):
    """
    Delete all images and spottings created in the last N hours.

    Args:
        hours: Number of hours to look back (default: 24)
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Transaction starten
        conn.autocommit = False

        # Zeitpunkt berechnen (letzte N Stunden)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        print(
            f"Lösche alle Bilder und Spottings seit {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # 1. Bilder der letzten N Stunden abrufen
        cur.execute(
            "SELECT id FROM images WHERE upload_timestamp >= %s;", (cutoff_time,)
        )
        image_ids_from_upload = [row[0] for row in cur.fetchall()]

        # 2. Spottings der letzten N Stunden abrufen (basierend auf detection_timestamp)
        cur.execute(
            "SELECT DISTINCT image_id FROM spottings WHERE detection_timestamp >= %s;",
            (cutoff_time,),
        )
        image_ids_from_spottings = [row[0] for row in cur.fetchall()]

        # Kombiniere beide Listen (alle betroffenen Images)
        all_image_ids = list(set(image_ids_from_upload + image_ids_from_spottings))

        # Prüfe ob es etwas zu löschen gibt
        if not image_ids_from_upload:
            print(
                f"Keine Bilder mit upload_timestamp in den letzten {hours} Stunden gefunden."
            )
        else:
            print(
                f"{len(image_ids_from_upload)} Bilder mit upload_timestamp >= {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} gefunden"
            )

        # 3. Spottings mit detection_timestamp in den letzten N Stunden löschen
        cur.execute(
            "DELETE FROM spottings WHERE detection_timestamp >= %s;", (cutoff_time,)
        )
        spottings_deleted = cur.rowcount
        print(
            f"  - {spottings_deleted} spottings mit detection_timestamp >= {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} gelöscht"
        )

        if not image_ids_from_upload and spottings_deleted == 0:
            print(f"Keine Daten in den letzten {hours} Stunden gefunden.")
            conn.rollback()
            return

        # 4. user_detections für alle betroffenen Images löschen
        if all_image_ids:
            cur.execute(
                "DELETE FROM user_detections WHERE image_id = ANY(%s);",
                (all_image_ids,),
            )
            user_detections_deleted = cur.rowcount
            print(f"  - {user_detections_deleted} user_detections gelöscht")
        else:
            user_detections_deleted = 0

        # 5. Images mit upload_timestamp in den letzten N Stunden löschen
        if image_ids_from_upload:
            cur.execute(
                "DELETE FROM images WHERE id = ANY(%s);", (image_ids_from_upload,)
            )
            images_deleted = cur.rowcount
            print(f"  - {images_deleted} images gelöscht")
        else:
            images_deleted = 0

        conn.commit()
        print(
            f"\nErfolgreich gelöscht: {images_deleted} Bilder, {spottings_deleted} Spottings, {user_detections_deleted} User-Detections"
        )

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Fehler: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    hours = 24
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print(f"Ungültige Stundenangabe: {sys.argv[1]}")
            print("Nutzung: python delete_recent_images.py [hours]")
            print("Standard: 24 Stunden")
            sys.exit(1)

    print(f"Lösche alle Bilder und Spottings der letzten {hours} Stunden...")
    delete_recent_images(hours)
