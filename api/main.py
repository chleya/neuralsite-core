# -*- coding: utf-8 -*-
"""
NeuralSite Core API
FastAPI入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from api.v1.routes import calculate
from api.v1.routes.knowledge import router as knowledge_router
from api.v1.routes.lod import router as lod_router


# 创建应用
app = FastAPI(
    title="NeuralSite Core API",
    description="公路参数化建模系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(calculate.router)
app.include_router(knowledge_router)
app.include_router(lod_router)


@app.get("/")
async def root():
    return {
        "name": "NeuralSite Core API",
        "version": "1.0.0",
        "description": "公路参数化建模系统",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
