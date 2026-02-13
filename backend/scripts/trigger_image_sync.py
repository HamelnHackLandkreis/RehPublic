#!/usr/bin/env python3
"""Manual trigger for image pull synchronization from all active sources."""

import argparse
import sys

from src.api.database import SessionLocal
from src.api.image_pull_sources.image_pull_service import ImagePullService


def trigger_sync(max_files: int = 10) -> None:
    """Trigger manual synchronization of all active image pull sources.

    Args:
        max_files: Maximum number of files to process per source
    """
    db = SessionLocal()
    try:
        print(f"🔄 Starting manual image sync (max {max_files} files per source)...")

        service = ImagePullService.factory()
        results = service.process_all_sources(db=db, max_files_per_source=max_files)

        total_processed = sum(r.get("processed_count", 0) for r in results)
        total_sources = len(results)

        print("\n✅ Sync completed!")
        print("\n📊 Summary:")
        print(f"   Sources processed: {total_sources}")
        print(f"   Total files processed: {total_processed}")

        if results:
            print("\n📂 Per-source results:")
            for source_result in results:
                status = source_result.get("status", "unknown")
                processed = source_result.get("processed_count", 0)
                source_name = source_result.get("source_name", "Unknown")

                print(f"   • {source_name}: {processed} files [{status}]")

                if source_result.get("error"):
                    print(f"     ⚠️  Error: {source_result['error']}")

    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Manually trigger image synchronization from all active sources"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="Maximum number of files to process per source (default: 10)",
    )

    args = parser.parse_args()

    trigger_sync(max_files=args.max_files)


if __name__ == "__main__":
    main()
