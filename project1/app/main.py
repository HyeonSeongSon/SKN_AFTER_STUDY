from fastapi import FastAPI
from .database import database, metadata, engine
from .crud_notes import router as notes_router
from .crud_recipes import router as recipes_router

# 테이블 생성
metadata.create_all(engine)

app = FastAPI(title="FastAPI + PostgreSQL Modular Example (Pydantic v2)")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# 라우터 등록
app.include_router(notes_router)
app.include_router(recipes_router)