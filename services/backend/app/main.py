from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.parse import router as parse_router
from app.routes.fill import router as fill_router
from app.routes.share import router as share_router
from app.routes.health import router as health_router

app = FastAPI(title="PDF MVP Backend")

app.include_router(upload_router, prefix="/upload")
app.include_router(parse_router, prefix="/parse")
app.include_router(fill_router, prefix="/fill")
app.include_router(share_router, prefix="/share")
app.include_router(health_router)
