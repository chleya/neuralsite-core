# -*- coding: utf-8 -*-
"""
LOD数据API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

import sys
sys.path.insert(0, '.')

from core.models.lod import (
    Project, Component, LODData, Coordinate3D, ConstructionInfo,
    create_subgrade, create_abnormal_column
)
from core.knowledge_graph.lod_graph import (
    save_component_to_graph, query_high_precision_points, init_lod_schema
)


router = APIRouter(prefix="/api/v1/lod", tags=["LOD数据"])


# ========== 请求模型 ==========

class CoordinateInput(BaseModel):
    x: float
    y: float
    z: float
    chainage: Optional[str] = None


class LODDataInput(BaseModel):
    level: int
    description: str
    key_points: Optional[List[CoordinateInput]] = []
    boundary_points: Optional[List[CoordinateInput]] = []
    critical_areas: Optional[List[Dict]] = []


class ConstructionInfoInput(BaseModel):
    fabrication_method: str = ""
    welding_points: Optional[List[CoordinateInput]] = []
    bolt_holes: Optional[List[Dict]] = []


class ComponentInput(BaseModel):
    component_id: str
    component_type: str
    description: str = ""
    parameters: Dict[str, Any] = {}
    lod_levels: List[LODDataInput] = []
    construction_info: Optional[ConstructionInfoInput] = None
    centerline: Optional[List[CoordinateInput]] = []


class ProjectInput(BaseModel):
    project_id: str
    coordinate_system: str = "CGCS2000"
    components: List[ComponentInput] = []


# ========== API端点 ==========

@router.post("/init-schema")
async def init_lod_schema_api():
    """初始化LOD图结构"""
    try:
        success = init_lod_schema()
        return {"status": "success" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/component")
async def create_component(component: ComponentInput):
    """创建构件"""
    try:
        # 转换输入
        comp = Component(
            component_id=component.component_id,
            component_type=component.component_type,
            description=component.description,
            parameters=component.parameters,
            centerline=[CoordinateInput(**c.dict()) for c in component.centerline] if component.centerline else []
        )
        
        # 添加LOD数据
        for lod_input in component.lod_levels:
            lod = LODData(
                level=lod_input.level,
                description=lod_input.description,
                key_points=[CoordinateInput(**p.dict()) for p in lod_input.key_points] if lod_input.key_points else [],
                boundary_points=[CoordinateInput(**p.dict()) for p in lod_input.boundary_points] if lod_input.boundary_points else [],
                critical_areas=lod_input.critical_areas
            )
            comp.add_lod(lod)
        
        # 添加施工信息
        if component.construction_info:
            ci = component.construction_info
            comp.construction_info = ConstructionInfo(
                fabrication_method=ci.fabrication_method,
                welding_points=[CoordinateInput(**p.dict()) for p in ci.welding_points] if ci.welding_points else [],
                bolt_holes=ci.bolt_holes
            )
        
        return {
            "status": "success",
            "component": comp.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/component/save")
async def save_component_to_neo4j(component: ComponentInput, project_id: str = "NS-001"):
    """保存构件到Neo4j"""
    try:
        # 创建组件
        comp = Component(
            component_id=component.component_id,
            component_type=component.component_type,
            description=component.description,
            parameters=component.parameters
        )
        
        # 添加LOD数据
        for lod_input in component.lod_levels:
            lod = LODData(
                level=lod_input.level,
                description=lod_input.description,
                key_points=[CoordinateInput(**p.dict()) for p in lod_input.key_points] if lod_input.key_points else [],
                boundary_points=[CoordinateInput(**p.dict()) for p in lod_input.boundary_points] if lod_input.boundary_points else [],
                critical_areas=lod_input.critical_areas
            )
            comp.add_lod(lod)
        
        # 保存到图数据库
        success = save_component_to_graph(comp, project_id)
        
        return {
            "status": "success" if success else "failed",
            "component_id": component.component_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/component/{component_id}/lod2")
async def get_lod2_points(component_id: str):
    """查询LOD2高精度点"""
    try:
        points = query_high_precision_points(component_id)
        return {
            "component_id": component_id,
            "lod": 2,
            "points": points
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo/abnormal-column")
async def demo_abnormal_column():
    """演示：创建异形柱"""
    # 创建异形柱
    column = create_abnormal_column(
        component_id="abnormal-column-demo",
        width=0.8,
        height=1.2,
        total_height=3.5,
        slope=0.05,
        corner_radius=0.1,
        material="Q345B"
    )
    
    # 添加LOD0
    column.add_lod(LODData(
        level=0,
        description="粗精度(米级)",
        key_points=[
            Coordinate3D(123.45, 678.90, 0.00),
            Coordinate3D(123.45, 678.90, 3.50)
        ]
    ))
    
    # 添加LOD1
    column.add_lod(LODData(
        level=1,
        description="中精度(分米级)",
        boundary_points=[
            Coordinate3D(123.45, 678.90, 0.00),
            Coordinate3D(123.65, 678.90, 0.00),
            Coordinate3D(123.65, 679.10, 0.00),
            Coordinate3D(123.45, 679.10, 0.00),
            Coordinate3D(123.45, 678.90, 3.50),
            Coordinate3D(123.65, 678.90, 3.50),
            Coordinate3D(123.65, 679.10, 3.50),
            Coordinate3D(123.45, 679.10, 3.50)
        ]
    ))
    
    # 添加LOD2
    column.add_lod(LODData(
        level=2,
        description="高精度(厘米级)",
        critical_areas=[
            {
                "areaName": "顶部连接区",
                "points": [
                    {"x": 123.450, "y": 678.900, "z": 3.450},
                    {"x": 123.455, "y": 678.905, "z": 3.455}
                ]
            },
            {
                "areaName": "底部锚固区",
                "points": [
                    {"x": 123.450, "y": 678.900, "z": 0.050},
                    {"x": 123.455, "y": 678.905, "z": 0.055}
                ]
            }
        ]
    ))
    
    # 施工信息
    column.construction_info = ConstructionInfo(
        fabrication_method="数控切割",
        welding_points=[
            Coordinate3D(123.45, 678.90, 1.0),
            Coordinate3D(123.45, 678.90, 2.0)
        ],
        bolt_holes=[
            {"diameter": 0.02, "depth": 0.1, "position": {"x": 123.45, "y": 678.90, "z": 3.3}},
            {"diameter": 0.02, "depth": 0.1, "position": {"x": 123.65, "y": 678.90, "z": 3.3}}
        ]
    )
    
    return {
        "message": "异形柱示例",
        "component": column.to_dict()
    }


@router.post("/demo/subgrade")
async def demo_subgrade():
    """演示：创建路基"""
    subgrade = create_subgrade(
        component_id="subgrade-demo",
        start_chainage="K0+000",
        end_chainage="K1+000",
        width=12.0,
        height=3.0
    )
    
    # 添加中心线
    subgrade.centerline = [
        Coordinate3D(500000, 3000000, 100, "K0+000"),
        Coordinate3D(500500, 3000353, 110, "K0+500"),
        Coordinate3D(501000, 3000707, 105, "K1+000")
    ]
    
    return {
        "message": "路基示例",
        "component": subgrade.to_dict()
    }
