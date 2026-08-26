from fastapi import FastAPI

app = FastAPI(title="AI Reserach and Code Intelligence Platform")

@app.get("/health")
def health_check():
    return {"status": "ok"}