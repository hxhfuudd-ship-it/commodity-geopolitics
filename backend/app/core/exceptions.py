from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class DataSourceError(Exception):
    def __init__(self, message: str = "数据源异常"):
        self.message = message


class AIServiceError(Exception):
    def __init__(self, message: str = "AI 服务异常"):
        self.message = message


class CacheError(Exception):
    def __init__(self, message: str = "缓存服务异常"):
        self.message = message


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(DataSourceError)
    async def data_source_handler(request: Request, exc: DataSourceError):
        logger.error(f"DataSourceError: {exc.message}")
        return JSONResponse(status_code=503, content={"detail": exc.message})

    @app.exception_handler(AIServiceError)
    async def ai_service_handler(request: Request, exc: AIServiceError):
        logger.error(f"AIServiceError: {exc.message}")
        return JSONResponse(status_code=503, content={"detail": exc.message})

    @app.exception_handler(CacheError)
    async def cache_handler(request: Request, exc: CacheError):
        logger.error(f"CacheError: {exc.message}")
        return JSONResponse(status_code=503, content={"detail": exc.message})
