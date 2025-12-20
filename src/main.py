from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.config import setup_logging, get_logger, settings
from src.storage import cache_manager, init_db
from src.api.routes import health_router, prediction_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Prediction Service...")
    
    await init_db()
    logger.info("Database initialized")
    
    await cache_manager.connect()
    
    yield
    
    await cache_manager.disconnect()
    logger.info("AI Prediction Service stopped")


app = FastAPI(
    title="AI Prediction Service",
    description="Cryptocurrency price prediction service using AI models",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(prediction_router)


@app.get("/")
async def root():
    return {
        "service": "AI Prediction Service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
