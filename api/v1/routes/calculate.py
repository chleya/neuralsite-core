# -*- coding: utf-8 -*-
"""
API路由 - 计算接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 导入核心模块
import sys
sys.path.insert(0, '.')

from core import NeuralSiteEngine
from agents.parser import DesignParser


router = APIRouter(prefix="/api/v1", tags=["计算"])


# ========== 数据模型 ==========

class CalculateRequest(BaseModel):
    """坐标计算请求"""
    route_id: str = Field(default="default", description="路线ID")
    station: float = Field(..., description="桩号(m)")
    lod: Optional[str] = Field(default="LOD1", description="LOD级别")


class CalculateRangeRequest(BaseModel):
    """批量计算请求"""
    route_id: str = Field(default="default")
    start: float = Field(..., description="起始桩号(m)")
    end: float = Field(..., description="结束桩号(m)")
    interval: float = Field(default=100, description="间隔(m)")


class CrossSectionRequest(BaseModel):
    """横断面计算请求"""
    station: float = Field(..., description="桩号(m)")
    offset: float = Field(default=0, description="横向偏移(m)")


class ParseTextRequest(BaseModel):
    """文本解析请求"""
    text: str = Field(..., description="输入文本")
    calculate: bool = Field(default=False, description="是否同时计算坐标")


# ========== 引擎实例管理 ==========

# 全局引擎字典
_engines = {}


def get_engine(route_id: str = "default") -> NeuralSiteEngine:
    """获取或创建引擎实例"""
    if route_id not in _engines:
        # 创建新引擎
        engine = NeuralSiteEngine(route_id)
        
        # 加载示例数据
        sample_data = {
            "route_id": route_id,
            "design_speed": 80,
            "horizontal_alignment": [
                {"element_type": "直线", "start_station": "K0+000", "end_station": "K0+500",
                 "azimuth": 45, "x0": 500000, "y0": 3000000},
                {"element_type": "缓和曲线", "start_station": "K0+500", "end_station": "K0+600",
                 "azimuth": 45, "x0": 500353.553, "y0": 3000353.553, "A": 300, "R": 800, "direction": "右"},
                {"element_type": "圆曲线", "start_station": "K0+600", "end_station": "K1+200",
                 "azimuth": 45, "x0": 500424.264, "y0": 3000424.264, "R": 800,
                 "cx": 500424.264, "cy": 3000224.264, "direction": "右"}
            ],
            "vertical_alignment": [
                {"station": "K0+000", "elevation": 100, "grade_out": 20},
                {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "length": 200},
                {"station": "K1+200", "elevation": 99.5, "grade_in": -15}
            ],
            "cross_section_template": {"width": 26, "lanes": 4, "crown_slope": 2.0}
        }
        
        engine.load_from_json(sample_data)
        _engines[route_id] = engine
    
    return _engines[route_id]


# ========== 路由 ==========

@router.get("/")
async def root():
    """根路径"""
    return {
        "name": "NeuralSite Core API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@router.post("/calculate")
async def calculate_coordinate(request: CalculateRequest):
    """
    计算单点坐标
    
    输入桩号，返回3D坐标
    """
    try:
        engine = get_engine(request.route_id)
        result = engine.get_coordinate_dict(request.station)
        
        return {
            "status": "success",
            "route_id": request.route_id,
            "lod": request.lod,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate/range")
async def calculate_range(request: CalculateRangeRequest):
    """
    批量计算坐标
    
    输入起止桩号和间隔，返回坐标数组
    """
    try:
        engine = get_engine(request.route_id)
        
        # LOD处理
        if request.interval <= 0:
            # 使用LOD
            results = engine.calculate_lod(request.start, request.end, "LOD1")
        else:
            results = engine.calculate_range(request.start, request.end, request.interval)
        
        return {
            "status": "success",
            "route_id": request.route_id,
            "start": request.start,
            "end": request.end,
            "interval": request.interval,
            "count": len(results),
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cross_section")
async def calculate_cross_section(request: CrossSectionRequest):
    """
    计算横断面
    
    输入桩号和偏移，返回断面点
    """
    try:
        engine = get_engine("default")
        result = engine.calculate_cross_section(request.station, request.offset)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse_text(request: ParseTextRequest):
    """
    解析文本参数
    
    输入工程文本，提取参数
    """
    try:
        parser = DesignParser()
        parsed = parser.parse_text(request.text)
        
        result = {
            "status": "success",
            "input": request.text,
            "parsed": parsed,
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果需要同时计算
        if request.calculate:
            engine = get_engine(request.route_id)
            engine.load_from_json(parser.to_engine_format())
            
            # 计算第一个桩号
            if parsed.get("horizontal"):
                first_station = parsed["horizontal"][0].get("start_station", "K0+000")
                station_m = int(first_station.split("+")[0][1:]) * 1000 + int(first_station.split("+")[1])
                coord = engine.get_coordinate_dict(station_m)
                result["coordinate"] = coord
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes")
async def list_routes():
    """列出所有路线"""
    return {
        "routes": list(_engines.keys()),
        "count": len(_engines)
    }
