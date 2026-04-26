from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.status import router as api_status_router
from app.api.routes_status import router as status_router
from app.api.routes_process import router as process_router

app = FastAPI(title="ParkViewRT Real Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router)
app.include_router(api_status_router)
app.include_router(process_router)


@app.get("/")
def root():
    return {"message": "ParkViewRT real backend is running"}
