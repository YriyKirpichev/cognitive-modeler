import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

count = 0

@app.get("/")
@app.head("/")
def health_check():
    return {"status": "ok"}

@app.get("/api/count")
def read_count():
    global count
    count += 1
    return {"count": count}

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)