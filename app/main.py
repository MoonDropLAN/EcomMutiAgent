from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.web.routes import router as web_router


def create_app() -> FastAPI:
    app = FastAPI(title="Multi-Agent Ecommerce Assistant")
    app.include_router(chat_router)
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()