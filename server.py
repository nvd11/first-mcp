import src.configs.config

from fastapi import FastAPI, Request
from loguru import logger
# from src.routers import async_router, test_router

app = FastAPI(root_path="/firstmcp")

# app.include_router(async_router.router)
# app.include_router(test_router.router)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed!")
    return {"message": "Hello, firstmcp!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
