from fastapi import FastAPI
from app.api.v1.router import api_router
from app.api.health import router as health_router

app = FastAPI(title="AI Reserach and Code Intelligence Platform")


app.include_router(health_router)
app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
