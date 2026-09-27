from fastapi import FastAPI

from app.api.v1.routers import auth, estoque, pedidos, produtos, unidades

app = FastAPI(
    title="Raízes do Nordeste API",
    version="0.1.0",
    description="API multicanal para a rede de lanchonetes Raízes do Nordeste.",
)

app.include_router(auth.router)
app.include_router(unidades.router)
app.include_router(produtos.router)
app.include_router(estoque.router)
app.include_router(pedidos.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
