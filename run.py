import uvicorn
from app.config.logging_config import LOGGING_CONFIG
from app.config.server_config import settings

if __name__ == "__main__":
    print(settings)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_config=LOGGING_CONFIG,
        log_level=settings.log_level,
    )
