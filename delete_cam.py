#!/usr/bin/env python3
import psycopg2
import sys

# ---------- CONFIG ----------
DB_CONFIG = {
    "host": "135.181.78.114",
    "port": 5432,
    "dbname": "rehpublic",
    "user": "rehpublic",
    "password": "hamelnhack2025"
}
# ----------------------------

def delete_location(location_id: str):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Transaktion starten
        conn.autocommit = False

        # 1. Bilder der Location abrufen
        cur.execute("SELECT id FROM images WHERE location_id = %s;", (location_id,))
        image_ids = [row[0] for row in cur.fetchall()]

        if not image_ids:
            print(f"Keine Bilder für Location {location_id} gefunden.")
        else:
            print(f"{len(image_ids)} Bilder gefunden – lösche zugehörige Daten ...")

        # 2. user_detections löschen
        cur.execute("DELETE FROM user_detections WHERE image_id = ANY(%s);", (image_ids,))

        # 3. spottings löschen
        cur.execute("DELETE FROM spottings WHERE image_id = ANY(%s);", (image_ids,))

        # 4. images löschen
        cur.execute("DELETE FROM images WHERE id = ANY(%s);", (image_ids,))

        # 5. location löschen
        cur.execute("DELETE FROM locations WHERE id = %s;", (location_id,))

        conn.commit()
        print(f"Location {location_id} und zugehörige Daten erfolgreich gelöscht.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Fehler: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Nutzung: python delete_location.py <location_id>")
        sys.exit(1)

    location_id = sys.argv[1]
    delete_location(location_id)
