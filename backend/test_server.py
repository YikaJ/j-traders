"""
简化的测试服务器
"""

from fastapi import FastAPI
import uvicorn

# 创建FastAPI应用实例
app = FastAPI(title="量化选股系统测试")

@app.get("/")
async def root():
    return {"message": "测试服务器运行正常"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("启动测试服务器...")
    uvicorn.run(
        "test_server:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )