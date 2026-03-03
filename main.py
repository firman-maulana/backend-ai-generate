from fastapi import FastAPI

app = FastAPI()

@app.get("/tes")
def health():
    return {"status": "ok"}