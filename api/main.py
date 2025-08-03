from fastapi import FastAPI
from api.routers import config, monitor

app = FastAPI(title="审计告警配置管理控制系统", version="1.0.0")

app.include_router(config.router, prefix="/api")
app.include_router(monitor.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "审计告警系统API服务正在运行"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "audit-alert-api"}

if __name__ == "__main__":
    import uvicorn
    from config.settings import API_HOST, API_PORT
    uvicorn.run(app, host=API_HOST, port=API_PORT)