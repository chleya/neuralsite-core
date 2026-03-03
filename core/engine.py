# -*- coding: utf-8 -*-
"""
NeuralSite Core Engine
参数化几何计算引擎
"""

import math
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from geometry import (
    HorizontalAlignment, VerticalAlignment, CrossSectionCalculator, CrossSectionTemplate,
    LineElement, CircularCurveElement, SpiralCurveElement,
    VerticalCurveElement
)


@dataclass
class Coordinate3D:
    """三维坐标"""
    station: float       # 桩号(m)
    x: float            # X坐标
    y: float            # Y坐标
    z: float            # 高程
    azimuth: float      # 方位角(度)
    
    def to_dict(self) -> Dict:
        return {
            "station": f"K{self.station//1000}+{self.station%1000:03d}",
            "station_m": self.station,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z": round(self.z, 3),
            "azimuth": round(self.azimuth, 3)
        }


@dataclass
class LODConfig:
    """LOD配置"""
    level: str           # LOD0/LOD1/LOD2
    interval: float      # 采样间隔(m)
    tolerance: float     # 容差(m)
    
    @classmethod
    def from_string(cls, level: str) -> 'LODConfig':
        configs = {
            "LOD0": cls(level="LOD0", interval=50, tolerance=0.5),
            "LOD1": cls(level="LOD1", interval=10, tolerance=0.05),
            "LOD2": cls(level="LOD2", interval=0.5, tolerance=0.01),
        }
        return configs.get(level, configs["LOD1"])


class NeuralSiteEngine:
    """NeuralSite核心计算引擎"""
    
    def __init__(self, route_id: str = ""):
        self.route_id = route_id
        self.horizontal = HorizontalAlignment()
        self.vertical = VerticalAlignment()
        self.cross_section = CrossSectionCalculator()
        self.design_speed = 80  # km/h
    
    # ========== 加载数据 ==========
    
    def load_from_json(self, data: Dict):
        """从JSON加载路线参数"""
        self.route_id = data.get("route_id", "")
        self.design_speed = data.get("design_speed", 80)
        
        # 加载平曲线
        for h in data.get("horizontal_alignment", []):
            elem_type = h.get("element_type", "直线")
            start_s = self._parse_station(h.get("start_station", "K0+000"))
            end_s = self._parse_station(h.get("end_station", "K0+000"))
            
            if elem_type == "直线":
                elem = LineElement(
                    start_s, end_s,
                    h.get("azimuth", 0),
                    h.get("x0", 0), h.get("y0", 0)
                )
            elif elem_type == "圆曲线":
                elem = CircularCurveElement(
                    start_s, end_s,
                    h.get("R", 0),
                    h.get("azimuth", 0),
                    h.get("x0", 0), h.get("y0", 0),
                    h.get("cx", 0), h.get("cy", 0),
                    h.get("direction", "右")
                )
            elif elem_type == "缓和曲线":
                elem = SpiralCurveElement(
                    start_s, end_s,
                    h.get("azimuth", 0),
                    h.get("x0", 0), h.get("y0", 0),
                    h.get("A", 0), h.get("R", 0),
                    h.get("direction", "右")
                )
            else:
                continue
            
            self.horizontal.add_element(elem)
        
        # 加载纵曲线
        for v in data.get("vertical_alignment", []):
            elem = VerticalCurveElement(
                station=self._parse_station(v.get("station", "K0+000")),
                elevation=v.get("elevation", 0),
                grade_in=v.get("grade_in", 0),
                grade_out=v.get("grade_out", 0),
                length=v.get("length", 0),
                curve_type=v.get("curve_type", "凸")
            )
            self.vertical.add_element(elem)
        
        # 加载横断面
        cs_data = data.get("cross_section_template", {})
        if cs_data:
            template = CrossSectionTemplate(
                width=cs_data.get("width", 26.0),
                lane_width=cs_data.get("lane_width", 3.75),
                lanes=cs_data.get("lanes", 4),
                crown_slope=cs_data.get("crown_slope", 2.0),
                side_slope=cs_data.get("side_slope", 1.5)
            )
            self.cross_section = CrossSectionCalculator(template)
    
    # ========== 核心计算 ==========
    
    def get_coordinate(self, station: float) -> Coordinate3D:
        """获取三维坐标
        
        Args:
            station: 桩号(m)
            
        Returns:
            Coordinate3D
        """
        x, y, azimuth = self.horizontal.get_coordinate(station)
        z = self.vertical.get_elevation(station)
        
        return Coordinate3D(
            station=station,
            x=x, y=y, z=z,
            azimuth=azimuth
        )
    
    def get_coordinate_dict(self, station: float) -> Dict:
        """获取三维坐标(字典)"""
        return self.get_coordinate(station).to_dict()
    
    def calculate_range(self, start: float, end: float, 
                        interval: float = 100) -> List[Dict]:
        """批量计算
        
        Args:
            start: 起始桩号(m)
            end: 结束桩号(m)
            interval: 间隔(m)
            
        Returns:
            坐标列表
        """
        results = []
        station = start
        while station <= end:
            results.append(self.get_coordinate_dict(station))
            station += interval
        return results
    
    def calculate_lod(self, start: float, end: float, 
                      lod: str = "LOD1") -> List[Dict]:
        """LOD计算
        
        Args:
            start: 起始桩号
            end: 结束桩号
            lod: LOD级别 (LOD0/LOD1/LOD2)
        """
        config = LODConfig.from_string(lod)
        return self.calculate_range(start, end, config.interval)
    
    def calculate_cross_section(self, station: float, offset: float = 0) -> Dict:
        """计算横断面
        
        Args:
            station: 桩号(m)
            offset: 横向偏移(m)
            
        Returns:
            断面点坐标
        """
        # 中心坐标
        coord = self.get_coordinate(station)
        
        # 计算超高
        # 简化: 查找当前桩号所在的圆曲线
        super_rate = 0
        for elem in self.horizontal.elements:
            if hasattr(elem, 'radius') and elem.radius:
                if elem.start_station <= station <= elem.end_station:
                    super_rate = self.cross_section.get_super_elevation_rate(
                        elem.radius, self.design_speed
                    )
                    break
        
        # 获取断面点
        points = self.cross_section.get_section_points(
            coord.x, coord.y, coord.z,
            coord.azimuth, station, offset,
            super_rate, 0
        )
        
        return {
            "station": f"K{station//1000}+{station%1000:03d}",
            "center": points['center'],
            "left_edge": points['left_edge'],
            "right_edge": points['right_edge'],
            "super_rate": super_rate
        }
    
    # ========== 工具方法 ==========
    
    def _parse_station(self, station_str: str) -> float:
        """解析桩号字符串"""
        import re
        m = re.search(r'K?(\d+)\+(\d{3})', str(station_str).upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0
    
    @property
    def start_station(self) -> float:
        """起点桩号"""
        return self.horizontal.start_station
    
    @property
    def end_station(self) -> float:
        """终点桩号"""
        return self.horizontal.end_station
    
    @property
    def total_length(self) -> float:
        """路线总长"""
        return self.horizontal.total_length


def create_engine_from_json(json_path: str) -> NeuralSiteEngine:
    """从JSON文件创建引擎"""
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    engine = NeuralSiteEngine(data.get("route_id", ""))
    engine.load_from_json(data)
    return engine


# 测试
if __name__ == "__main__":
    # 创建引擎
    engine = NeuralSiteEngine("TEST_ROAD")
    
    # 示例数据
    sample_data = {
        "route_id": "TEST_ROAD",
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
        "cross_section_template": {
            "width": 26, "lanes": 4, "crown_slope": 2.0
        }
    }
    
    engine.load_from_json(sample_data)
    
    print("=== NeuralSite Engine Test ===\n")
    
    # 测试坐标计算
    for s in [0, 250, 500, 600, 800, 1000, 1200]:
        coord = engine.get_coordinate(s)
        print(f"{coord.to_dict()['station']}: X={coord.x:.2f} Y={coord.y:.2f} Z={coord.z:.2f}")
    
    # 测试横断面
    print("\n=== Cross Section ===")
    cs = engine.calculate_cross_section(500)
    print(f"Center: {cs['center']}")
    print(f"Super elevation: {cs['super_rate']:.2f}%")
