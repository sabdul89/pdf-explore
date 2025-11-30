from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.parse import router as parse_router
from app.routes.fill import router as fill_router
from app.routes.flatten import router as flatten_router
from app.routes.share import router as share_router
from app.routes.health import router as health_router

app = FastAPI(title="PDF Explore Backend - Enterprise OCR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow ALL frontends
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


app.include_router(upload_router)
app.include_router(parse_router)
app.include_router(fill_router)
app.include_router(flatten_router)
app.include_router(share_router)
app.include_router(health_router)
