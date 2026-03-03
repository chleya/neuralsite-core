# -*- coding: utf-8 -*-
"""
数据导入API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
import json

import sys
sys.path.insert(0, '.')

from core.data_import.excel_importer import parse_excel_file, ExcelRoadImporter


router = APIRouter(prefix="/api/v1/import", tags=["数据导入"])


class ImportResult(BaseModel):
    """导入结果"""
    status: str
    route_id: str
    points_count: int = 0
    elements_count: int = 0
    message: str = ""


@router.post("/excel/road")
async def import_excel_road(
    file: UploadFile = File(...)
):
    """导入Excel道路数据
    
    支持的表格格式:
    - 逐桩坐标表 (桩号, X, Y, Z)
    - 平曲线参数表 (交点号, 桩号, 半径R, 缓和曲线A)
    - 竖曲线参数表 (变坡点桩号, 标高, 坡度)
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 解析Excel
        result = parse_excel_file(content)
        
        # 返回结果
        return {
            "status": "success",
            "route_id": result.get("route_id", "imported"),
            "horizontal_count": len(result.get("horizontal_alignment", [])),
            "vertical_count": len(result.get("vertical_alignment", [])),
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/excel/demo")
async def get_excel_demo():
    """获取Excel导入示例数据"""
    from core.data_import.excel_importer import DEMO_EXCEL_DATA
    
    return {
        "format": "CSV",
        "description": "逐桩坐标表示例",
        "columns": ["桩号", "X", "Y", "Z"],
        "data": DEMO_EXCEL_DATA
    }


@router.post("/json/road")
async def import_json_road(
    data: dict = Form(...)
):
    """导入JSON格式道路数据
    
    直接传入NeuralSite格式的路线参数
    """
    try:
        # 验证必要字段
        if "horizontal_alignment" not in data:
            raise ValueError("Missing horizontal_alignment")
        
        return {
            "status": "success",
            "route_id": data.get("route_id", "imported"),
            "message": "JSON数据导入成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/text/parse")
async def parse_text_design(
    text: str = Form(..., description="设计文本")
):
    """解析文本格式的设计参数
    
    支持格式:
    - "R=800, A=300, K0+000"
    - "主线: R=800, LS=120"
    """
    try:
        from agents.parser import DesignParser
        
        parser = DesignParser()
        result = parser.parse_text(text)
        
        return {
            "status": "success",
            "input": text,
            "parsed": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def list_supported_formats():
    """列出支持的数据导入格式"""
    return {
        "formats": [
            {
                "id": "excel",
                "name": "Excel",
                "extensions": [".xlsx", ".xls"],
                "description": "支持逐桩坐标表、平曲线表、竖曲线表"
            },
            {
                "id": "json",
                "name": "JSON",
                "extensions": [".json"],
                "description": "NeuralSite标准JSON格式"
            },
            {
                "id": "text",
                "name": "Text",
                "extensions": [".txt"],
                "description": "自然语言描述的设计参数"
            },
            {
                "id": "dxf",
                "name": "DXF",
                "extensions": [".dxf"],
                "description": "AutoCAD DXF格式 (开发中)"
            }
        ]
    }
