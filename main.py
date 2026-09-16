from fastapi import FastAPI

app = FastAPI(
    title="Raízes do Nordeste API",
    description="API multicanal para a rede de lanchonetes Raízes do Nordeste.",
)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok"}
