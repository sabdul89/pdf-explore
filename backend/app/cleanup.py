import datetime
import logging
from app.supabase_client import supabase
from app.config import SUPABASE_BUCKET
from app.storage import upload_to_bucket  # for consistency
from supabase import create_client

# Optional: Improve logging output
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CLEANUP] %(message)s")


def delete_storage_file(path: str):
    """
    Deletes a file from Supabase storage.
    """
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([path])
        logging.info(f"Deleted storage file: {path}")
    except Exception as e:
        logging.error(f"Failed to delete {path}: {e}")


def run_cleanup():
    now = datetime.datetime.utcnow().isoformat()

    logging.info("Starting cleanup job...")

    # ------------------------------------------
    # 1. DELETE EXPIRED SHARE LINKS
    # ------------------------------------------
    expired_links = supabase.table("shares") \
        .select("*") \
        .lt("expires_at", now) \
        .execute()

    if expired_links.data:
        logging.info(f"Found {len(expired_links.data)} expired share links.")

        for row in expired_links.data:
            token = row["token"]
            file_id = row["file_id"]
            logging.info(f"Deleting expired share link: {token} (file {file_id})")

            supabase.table("shares").delete().eq("token", token).execute()
    else:
        logging.info("No expired share links found.")

    # ------------------------------------------
    # 2. DELETE EXPIRED FILE RECORDS
    # ------------------------------------------
    expired_files = supabase.table("files") \
        .select("*") \
        .lt("expires_at", now) \
        .execute()

    if expired_files.data:
        logging.info(f"Found {len(expired_files.data)} expired files.")

        for row in expired_files.data:
            file_id = row["file_id"]

            # Remove associated files from bucket
            original_path = f"original/{file_id}.pdf"
            filled_path = f"filled/{file_id}.pdf"

            delete_storage_file(original_path)
            delete_storage_file(filled_path)

            # Delete DB entry
            logging.info(f"Deleting file record: {file_id}")
            supabase.table("files").delete().eq("file_id", file_id).execute()
    else:
        logging.info("No expired file records.")

    logging.info("Cleanup job complete.")


if __name__ == "__main__":
    run_cleanup()
