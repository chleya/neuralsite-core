# -*- coding: utf-8 -*-
"""
工程智能API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

import sys
sys.path.insert(0, '.')

from core.engineering.engine import (
    get_engineering_intel, 
    ConstructionRecommendation,
    QualityControl
)


router = APIRouter(prefix="/api/v1/engineering", tags=["工程智能"])


# ========== 请求模型 ==========

class ConstructionRecommendRequest(BaseModel):
    """施工工艺推荐请求"""
    component_type: str = Field(..., description="构件类型")
    material: str = Field(default="Q345B", description="材料")
    complexity: str = Field(default="high", description="复杂度")
    size: Optional[Dict[str, float]] = Field(default=None, description="尺寸")
    site_conditions: Optional[Dict[str, Any]] = Field(default=None, description="现场条件")


class CollisionDetectionRequest(BaseModel):
    """碰撞检测请求"""
    component1: Dict[str, Any]
    component2: Dict[str, Any]
    lod_level: int = Field(default=1, description="LOD精度级别")


class BIMExportRequest(BaseModel):
    """BIM导出请求"""
    component: Dict[str, Any]
    format: str = Field(default="revit", description="BIM格式: revit/tekla/ifc")


# ========== API端点 ==========

@router.post("/recommend-construction")
async def recommend_construction(request: ConstructionRecommendRequest):
    """施工工艺推荐
    
    根据构件参数自动推荐最佳施工方法
    """
    try:
        engine = get_engineering_intel()
        
        recommendations = engine.recommend_construction_method(
            component_type=request.component_type,
            material=request.material,
            complexity=request.complexity,
            size=request.size,
            site_conditions=request.site_conditions
        )
        
        return {
            "component_type": request.component_type,
            "recommendations": [
                {
                    "method": rec.method,
                    "confidence": rec.confidence,
                    "reasons": rec.reasons,
                    "constraints": rec.constraints,
                    "resources": rec.resources
                }
                for rec in recommendations
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collision-detection")
async def collision_detection(request: CollisionDetectionRequest):
    """碰撞检测
    
    检测两个构件是否发生碰撞
    LOD0: 米级快速检测
    LOD1: 分米级常规检测  
    LOD2: 厘米级精确检测
    """
    try:
        engine = get_engineering_intel()
        
        result = engine.detect_collision(
            component1=request.component1,
            component2=request.component2,
            lod_level=request.lod_level
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-bim-model")
async def generate_bim_model(request: BIMExportRequest):
    """BIM模型生成
    
    将构件参数转换为BIM格式
    支持: Revit参数化族, Tekla模型, IFC
    """
    try:
        engine = get_engineering_intel()
        
        bim_data = engine.export_to_bim_format(
            component=request.component,
            format=request.format
        )
        
        return {
            "format": request.format,
            "data": bim_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality-control/{component_id}")
async def generate_quality_control(component_id: str, component: Dict[str, Any]):
    """质量控制计划
    
    根据构件生成质量控制点
    """
    try:
        engine = get_engineering_intel()
        
        qc_points = engine.generate_quality_control_plan(component)
        
        return {
            "component_id": component_id,
            "quality_control_points": [
                {
                    "point_id": qc.point_id,
                    "name": qc.name,
                    "standard_value": qc.standard_value,
                    "tolerance": qc.tolerance,
                    "test_method": qc.test_method,
                    "location": qc.location
                }
                for qc in qc_points
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/methods")
async def list_construction_methods():
    """列出所有支持的施工工艺"""
    return {
        "methods": [
            {"id": "cnc_cutting", "name": "数控切割", "description": "高精度自动化切割"},
            {"id": "field_welding", "name": "现场焊接", "description": "现场拼接作业"},
            {"id": "prefabrication", "name": "预制装配", "description": "工厂预制现场装配"},
            {"id": "cast_in_place", "name": "现浇混凝土", "description": "现场浇筑"},
            {"id": "lifting", "name": "整体吊装", "description": "大型构件吊装"}
        ]
    }


@router.get("/formats")
async def list_bim_formats():
    """列出所有支持的BIM格式"""
    return {
        "formats": [
            {"id": "revit", "name": "Revit", "description": "Autodesk Revit参数化族"},
            {"id": "tekla", "name": "Tekla Structures", "description": "钢结构模型"},
            {"id": "ifc", "name": "IFC", "description": "开放BIM格式"}
        ]
    }


# ========== 演示端点 ==========

@router.post("/demo/abnormal-column-recommend")
async def demo_abnormal_column_recommend():
    """演示：异形柱施工推荐"""
    
    engine = get_engineering_intel()
    
    component = {
        "type": "AbnormalColumn",
        "componentId": "abnormal-001",
        "parameters": {
            "width": 0.8,
            "height": 1.2,
            "totalHeight": 3.5,
            "material": "Q345B",
            "slope": 0.05
        }
    }
    
    recommendations = engine.recommend_construction_method(
        component_type="AbnormalColumn",
        material="Q345B",
        complexity="high"
    )
    
    return {
        "component": component,
        "recommendations": [
            {
                "method": rec.method,
                "confidence": rec.confidence,
                "reasons": rec.reasons,
                "constraints": rec.constraints,
                "resources": rec.resources
            }
            for rec in recommendations
        ]
    }


@router.post("/demo/collision-test")
async def demo_collision_test():
    """演示：碰撞检测"""
    
    engine = get_engineering_intel()
    
    # 两个相近的构件
    component1 = {
        "componentId": "col-001",
        "parameters": {"x": 100.0, "y": 200.0, "z": 0.0, "size": 1.0}
    }
    
    component2 = {
        "componentId": "col-002", 
        "parameters": {"x": 100.5, "y": 200.3, "z": 0.2, "size": 1.0}
    }
    
    results = {}
    for lod in [0, 1, 2]:
        results[f"lod_{lod}"] = engine.detect_collision(component1, component2, lod)
    
    return {
        "component1": component1,
        "component2": component2,
        "results": results
    }
