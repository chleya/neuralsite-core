# -*- coding: utf-8 -*-
"""
知识图谱API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

import sys
sys.path.insert(0, '.')

from core.knowledge_graph.schema import (
    init_schema, query_elevation, create_project, create_drawing, 
    create_feature, link_feature_to_coordinate
)
from storage.graph_db import get_graph_db


router = APIRouter(prefix="/api/v1/knowledge", tags=["知识图谱"])


class QueryRequest(BaseModel):
    """知识查询请求"""
    question: str = Field(..., description="问题")


class EntityRequest(BaseModel):
    """实体创建请求"""
    project: str = Field(..., description="项目名")
    drawing: str = Field(..., description="图纸名")
    drawing_type: str = Field(..., description="图纸类型")
    feature_id: str = Field(..., description="特征ID")
    feature_type: str = Field(..., description="特征类型")
    chainage: str = Field(..., description="桩号")
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    z: float = Field(..., description="高程")


@router.post("/init")
async def init_knowledge_graph():
    """初始化知识图谱结构"""
    try:
        success = init_schema()
        return {"status": "success" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_knowledge(request: QueryRequest):
    """查询知识
    
    支持的查询：
    - "K0+500的设计标高是多少"
    - "K1+200的坐标"
    """
    try:
        # 简单解析：从问题中提取桩号
        import re
        question = request.question
        
        # 提取桩号
        match = re.search(r'K(\d+)\+(\d{3})', question)
        if not match:
            return {"answer": "无法从问题中提取桩号"}
        
        chainage = f"K{match.group(1)}+{match.group(2)}"
        
        # 查询高程
        elevation = query_elevation(chainage)
        
        if elevation is not None:
            return {
                "answer": f"{chainage}的设计高程是{elevation}m",
                "chainage": chainage,
                "elevation": elevation
            }
        else:
            return {
                "answer": f"未找到{chainage}的数据",
                "chainage": chainage
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entity")
async def create_entity(request: EntityRequest):
    """创建工程实体并关联坐标"""
    try:
        # 创建项目
        create_project(request.project)
        
        # 创建图纸
        create_drawing(request.project, request.drawing, request.drawing_type)
        
        # 创建特征
        create_feature(request.drawing, request.feature_id, request.feature_type, request.chainage)
        
        # 关联坐标
        link_feature_to_coordinate(request.feature_id, request.x, request.y, request.z, request.chainage)
        
        return {
            "status": "success",
            "message": f"已创建{request.chainage}的实体和坐标"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_connection():
    """测试图数据库连接"""
    db = get_graph_db()
    if db.driver:
        result = db.execute_query("RETURN 1 as test")
        return {"status": "connected", "test": result}
    else:
        return {"status": "not_connected"}
