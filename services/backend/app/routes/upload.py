@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Validate extension
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        # Save temporary file
        file_id = str(uuid.uuid4())
        temp_path = f"/tmp/{file_id}.pdf"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # ---- Upload to Supabase Storage (fix here) ----
        storage_path = f"original/{file_id}.pdf"
        upload_res = supabase.storage.from_(SUPABASE_BUCKET).upload(
            storage_path,
            temp_path
        )

        # Correct check (UploadResponse object)
        if upload_res is None or getattr(upload_res, "error", None):
            raise HTTPException(
                status_code=500,
                detail="Supabase storage upload failed."
            )

        # Hybrid extraction
        fields = extract_hybrid(temp_path)

        # Insert DB row
        record = {
            "file_id": file_id,
            "storage_path": storage_path,
            "original_filename": file.filename,
            "status": "uploaded",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).isoformat()
        }

        db_res = supabase.table("files").insert(record).execute()

        if hasattr(db_res, "error") and db_res.error:
            raise HTTPException(
                status_code=500,
                detail=f"DB insert failed: {db_res.error.message}"
            )

        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {
            "file_id": file_id,
            "storage_path": storage_path,
            "fields": fields
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
