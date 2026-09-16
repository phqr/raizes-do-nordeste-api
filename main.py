from fastapi import FastAPI

from app.api.v1.routers import auth

app = FastAPI(
    title="Raízes do Nordeste API",
    description="API multicanal para a rede de lanchonetes Raízes do Nordeste.",
)

app.include_router(auth.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok"}
