# -*- coding: utf-8 -*-
"""
工作流API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

import sys
sys.path.insert(0, '.')

from core.agents.workflow import get_workflow_engine, WorkflowEngine
from core.agents.qa_agent import get_qa_agent


router = APIRouter(prefix="/api/v1/workflow", tags=["工作流"])


class PipelineRequest(BaseModel):
    """完整管道请求"""
    route_data: dict = Field(..., description="路线数据")
    start: float = Field(default=0, description="起始桩号(m)")
    end: float = Field(default=1200, description="结束桩号(m)")
    interval: float = Field(default=50, description="间隔(m)")


class ValidationRequest(BaseModel):
    """质检请求"""
    route_data: dict = Field(..., description="路线数据")
    coordinates: list = Field(..., description="坐标列表")


@router.post("/run")
async def run_full_pipeline(request: PipelineRequest):
    """运行完整管道
    
    自动执行: 导入 -> 计算坐标 -> 质检 -> 生成报告
    """
    try:
        engine = get_workflow_engine()
        result = engine.run_import_validate_pipeline(
            request.route_data,
            request.start,
            request.end,
            request.interval
        )
        
        if result.success:
            return {
                "status": "success",
                "route_id": result.route_id,
                "coordinates": result.coordinates,
                "qa_report": result.qa_report
            }
        else:
            return {
                "status": "error",
                "error": result.error
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def run_validation(request: ValidationRequest):
    """仅运行质检
    
    已有坐标数据时，直接进行质检
    """
    try:
        qa = get_qa_agent()
        report = qa.run_full_validation(
            request.route_data,
            request.coordinates
        )
        
        return {
            "status": "success",
            "report": {
                "report_id": report.report_id,
                "route_id": report.route_id,
                "status": report.status,
                "total_points": report.total_points,
                "issues_count": report.issues_count,
                "summary": report.summary,
                "issues": [
                    {
                        "id": i.issue_id,
                        "severity": i.severity.value,
                        "location": i.location,
                        "type": i.issue_type,
                        "description": i.description,
                        "recommendation": i.recommendation
                    }
                    for i in report.issues
                ]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def get_validation_rules():
    """获取验证规则"""
    qa = get_qa_agent()
    
    return {
        "rules": [
            {
                "name": "radius_min",
                "description": "曲线半径不能为0",
                "severity": "error"
            },
            {
                "name": "radius_too_small",
                "description": "半径过小 (<15m)",
                "severity": "warning"
            },
            {
                "name": "slope_too_steep",
                "description": "纵坡超过5%",
                "severity": "warning"
            },
            {
                "name": "point_spacing_max",
                "description": "桩点间距超过200m",
                "severity": "warning"
            }
        ]
    }


@router.post("/demo")
async def demo_workflow():
    """演示：运行完整工作流"""
    # 演示数据
    route_data = {
        "route_id": "demo_route",
        "horizontal_alignment": [
            {
                "element_type": "直线",
                "start_station": "K0+000",
                "end_station": "K0+500",
                "azimuth": 45,
                "x0": 500000,
                "y0": 3000000
            },
            {
                "element_type": "直线",
                "start_station": "K0+500",
                "end_station": "K1+000",
                "azimuth": 45,
                "x0": 500353.553,
                "y0": 3000353.553
            }
        ],
        "vertical_alignment": [
            {"station": "K0+000", "elevation": 100, "grade_out": 20},
            {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "length": 200},
            {"station": "K1+000", "elevation": 102.5, "grade_in": -15}
        ]
    }
    
    # 坐标数据
    coordinates = [
        {"station": "K0+000", "x": 500000, "y": 3000000, "z": 100},
        {"station": "K0+250", "x": 500176, "y": 3000176, "z": 105},
        {"station": "K0+500", "x": 500353, "y": 3000353, "z": 110},
        {"station": "K0+750", "x": 500530, "y": 3000530, "z": 107.5},
        {"station": "K1+000", "x": 500707, "y": 3000707, "z": 102.5}
    ]
    
    # 运行质检
    qa = get_qa_agent()
    report = qa.run_full_validation(route_data, coordinates)
    
    return {
        "message": "工作流演示",
        "route_id": "demo_route",
        "coordinates_count": len(coordinates),
        "qa_result": {
            "status": report.status,
            "issues_count": report.issues_count,
            "summary": report.summary
        }
    }
