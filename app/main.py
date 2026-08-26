from fastapi import FastAPI
import app.api.document as document

app = FastAPI(title="AI Reserach and Code Intelligence Platform")

app.include_router(document.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
