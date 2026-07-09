"""Pydantic 模型：定义 API 收发数据的结构。

对应文档：docs/06-fastapi-advanced.md 第 1-2 节、docs/07 第 3 节
"""
from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """POST /todos 的请求体（新建时客户端发来的数据，没有 id）。"""
    title: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    done: bool = False


class TodoUpdate(BaseModel):
    """PUT /todos/{id} 的请求体（所有字段可选，只更新提供的字段）。"""
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    done: bool | None = None


class TodoOut(BaseModel):
    """所有接口返回的待办数据（数据库里的完整记录，有 id）。"""
    id: int
    title: str
    description: str
    done: bool
