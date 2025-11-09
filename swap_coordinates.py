#!/usr/bin/env python3
"""
Script to swap longitude and latitude for specific locations:
- Bessinger Klippen
- Schweineberg Nord
"""

import psycopg2
import sys

# ---------- CONFIG ----------
DB_CONFIG = {
    "host": "135.181.78.114",
    "port": 5432,
    "dbname": "rehpublic",
    "user": "rehpublic",
    "password": "hamelnhack2025",
}
# ----------------------------

# Location IDs and names
LOCATIONS_TO_FIX = [
    {
        "id": "99d248b5-d117-42d6-85c4-dbe42e7803e9",
        "name": "Bessinger Klippen",
    },
    {
        "id": "a546e467-bf2c-4f2a-9e33-0eeb2f766bfd",
        "name": "Schweineberg Nord",
    },
]


def swap_coordinates():
    """Swap longitude and latitude for the specified locations."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Transaction starten
        conn.autocommit = False

        for location in LOCATIONS_TO_FIX:
            location_id = location["id"]
            location_name = location["name"]

            # Aktuelle Koordinaten abrufen
            cur.execute(
                "SELECT longitude, latitude FROM locations WHERE id = %s;",
                (location_id,),
            )
            result = cur.fetchone()

            if not result:
                print(f"Location {location_name} ({location_id}) nicht gefunden.")
                continue

            current_longitude, current_latitude = result
            print(f"{location_name} ({location_id}):")
            print(
                f"  Aktuell: longitude={current_longitude}, latitude={current_latitude}"
            )

            # Koordinaten tauschen
            cur.execute(
                """
                UPDATE locations 
                SET longitude = %s, latitude = %s 
                WHERE id = %s;
                """,
                (current_latitude, current_longitude, location_id),
            )

            print(
                f"  Geändert: longitude={current_latitude}, latitude={current_longitude}"
            )
            print()

        conn.commit()
        print("Koordinaten erfolgreich getauscht.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Fehler: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Tausche Koordinaten für Bessinger Klippen und Schweineberg Nord...")
    print()
    swap_coordinates()
