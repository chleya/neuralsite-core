# -*- coding: utf-8 -*-
"""
空间数据API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

import sys
sys.path.insert(0, '.')

from core.spatial.database import SpatialPoint, get_spatial_db


router = APIRouter(prefix="/api/v1/spatial", tags=["空间数据"])


class AddPointRequest(BaseModel):
    """添加空间点请求"""
    project_id: int
    chainage: str = Field(..., description="桩号")
    point_type: str = Field(..., description="点类型")
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    z: float = Field(default=0, description="高程")
    azimuth: float = Field(default=0, description="方位角")
    properties: dict = Field(default_factory=dict, description="其他属性")


class QueryNearbyRequest(BaseModel):
    """附近查询请求"""
    x: float = Field(..., description="中心点X")
    y: float = Field(..., description="中心点Y")
    radius: float = Field(default=100, description="查询半径(米)")
    project_id: Optional[int] = Field(default=None, description="项目ID")


@router.post("/point")
async def add_spatial_point(request: AddPointRequest):
    """添加空间点"""
    try:
        db = get_spatial_db()
        
        point = SpatialPoint(
            id=None,
            project_id=request.project_id,
            chainage=request.chainage,
            point_type=request.point_type,
            x=request.x,
            y=request.y,
            z=request.z,
            azimuth=request.azimuth,
            properties=request.properties
        )
        
        point_id = db.add_point(point)
        
        return {
            "status": "success",
            "point_id": point_id,
            "chainage": request.chainage
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nearby")
async def query_nearby(request: QueryNearbyRequest):
    """查询附近的空间点"""
    try:
        db = get_spatial_db()
        
        points = db.query_nearby(
            request.x,
            request.y,
            request.radius,
            request.project_id
        )
        
        return {
            "status": "success",
            "count": len(points),
            "points": [
                {
                    "id": p.id,
                    "chainage": p.chainage,
                    "point_type": p.point_type,
                    "x": p.x,
                    "y": p.y,
                    "z": p.z,
                    "azimuth": p.azimuth
                }
                for p in points
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chainage/{project_id}")
async def query_by_chainage(
    project_id: int,
    start: str = "K0+000",
    end: str = "K1+000"
):
    """按桩号范围查询"""
    try:
        db = get_spatial_db()
        
        points = db.query_by_chainage(start, end, project_id)
        
        return {
            "status": "success",
            "count": len(points),
            "start": start,
            "end": end,
            "points": [
                {
                    "chainage": p.chainage,
                    "point_type": p.point_type,
                    "x": p.x,
                    "y": p.y,
                    "z": p.z
                }
                for p in points
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo")
async def demo_spatial():
    """演示：添加测试数据并查询"""
    db = get_spatial_db()
    
    # 添加测试点
    test_points = [
        SpatialPoint(None, 1, "K0+000", "centerline", 500000, 3000000, 100, 45),
        SpatialPoint(None, 1, "K0+100", "centerline", 500070, 3000070, 102, 45),
        SpatialPoint(None, 1, "K0+200", "centerline", 500141, 3000141, 104, 45),
        SpatialPoint(None, 1, "K0+300", "centerline", 500212, 3000212, 106, 45),
        SpatialPoint(None, 1, "K0+400", "centerline", 500282, 3000282, 108, 45),
        SpatialPoint(None, 1, "K0+500", "centerline", 500353, 3000353, 110, 45),
    ]
    
    for p in test_points:
        db.add_point(p)
    
    # 查询附近 K0+300 的点
    nearby = db.query_nearby(500212, 3000212, 200, project_id=1)
    
    return {
        "message": "空间数据演示",
        "total_points": 6,
        "nearby_count": len(nearby),
        "nearby_points": [
            {"chainage": p.chainage, "x": p.x, "y": p.y}
            for p in nearby
        ]
    }
