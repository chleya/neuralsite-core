# -*- coding: utf-8 -*-
"""
AI解析器 - DesignParser
负责从文本/CAD中提取参数
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ParsedHorizontal:
    """解析后的平曲线参数"""
    element_type: str = "直线"     # 直线/缓和曲线/圆曲线
    start_station: float = 0       # 起点桩号(m)
    end_station: float = 0         # 终点桩号(m)
    azimuth: float = 0              # 方位角(度)
    R: float = 0                   # 半径(m)
    A: float = 0                   # 回旋参数
    Ls: float = 0                  # 缓和曲线长(m)
    x0: float = 0                  # 起点X
    y0: float = 0                  # 起点Y
    direction: str = "右"           # 转向


@dataclass
class ParsedVertical:
    """解析后的纵曲线参数"""
    station: float = 0              # 变坡点桩号(m)
    elevation: float = 0             # 高程(m)
    grade_in: float = 0             # 入口坡度(‰)
    grade_out: float = 0            # 出口坡度(‰)
    length: float = 0               # 竖曲线长度(m)
    curve_type: str = "凸"          # 凸/凹


@dataclass
class ParsedCrossSection:
    """解析后的横断面参数"""
    width: float = 26.0              # 路基宽度(m)
    lanes: int = 4                  # 车道数
    crown_slope: float = 2.0         # 路拱坡(%)
    side_slope: float = 1.5         # 边坡坡率
    superelevation: float = 8.0      # 超高(%)


class DesignParser:
    """
    工程图纸语义解析器
    
    功能：
    1. 文本解析：从字符串中提取参数
    2. 语义提取：使用正则表达式提取工程参数
    3. 结构化输出：输出标准格式的Dict
    """
    
    # 正则表达式模式
    PATTERNS = {
        # 桩号: K0+000, K1+500, ZK0+000
        'station': re.compile(r'([KZ]?K?)(\d+)\+(\d{3})', re.IGNORECASE),
        
        # 半径: R=500, R=800m, 半径500米
        'radius': re.compile(r'R\s*[=：]?\s*(\d+\.?\d*)\s*m?', re.IGNORECASE),
        
        # 回旋参数: A=300, A:300
        'A': re.compile(r'A\s*[=：]?\s*(\d+\.?\d*)', re.IGNORECASE),
        
        # 缓和曲线长: LS=100, Ls=80, LS=120m
        'Ls': re.compile(r'L[Ss]\s*[=：]?\s*(\d+\.?\d*)\s*m?', re.IGNORECASE),
        
        # 坡度: i=20, i=3.5%, 坡度20‰
        'grade': re.compile(r'i\s*[=：]?\s*([+-]?\d+\.?\d*)\s*[%‰]?', re.IGNORECASE),
        
        # 高程: H=100.5, 高程=125.5m
        'elevation': re.compile(r'(?:H|高程)\s*[=：]?\s*(\d+\.?\d*)\s*m?', re.IGNORECASE),
        
        # 方位角: Az=45, 方位角=90°
        'azimuth': re.compile(r'(?:Az|方位角)\s*[=：]?\s*(\d+\.?\d*)\s*[°]?', re.IGNORECASE),
        
        # 宽度: W=26, 宽=26米
        'width': re.compile(r'W\s*[=：]?\s*(\d+\.?\d*)\s*m?', re.IGNORECASE),
        
        # 跨径: 4x30, 4x30m
        'spans': re.compile(r'(\d+)\s*[×x]\s*(\d+)\s*m?', re.IGNORECASE),
    }
    
    def __init__(self):
        self.parsed_data = {}
    
    def parse_text(self, input_text: str) -> Dict:
        """
        解析文本，提取参数
        
        Args:
            input_text: 输入文本，例如：
                '主线: R=800, LS=120, A=300, 起点: K0+000'
                
        Returns:
            包含提取参数的字典
        """
        text = input_text.upper()
        
        result = {
            "horizontal": [],
            "vertical": [],
            "cross_section": {},
            "structures": []
        }
        
        # 提取桩号
        stations = self._extract_stations(text)
        
        # 提取平曲线参数
        horizontal = self._extract_horizontal(text, stations)
        if horizontal:
            result["horizontal"] = horizontal
        
        # 提取纵曲线参数
        vertical = self._extract_vertical(text, stations)
        if vertical:
            result["vertical"] = vertical
        
        # 提取横断面参数
        cs = self._extract_cross_section(text)
        if cs:
            result["cross_section"] = cs
        
        # 验证必要参数
        self._validate(result)
        
        self.parsed_data = result
        return result
    
    def _extract_stations(self, text: str) -> list:
        """提取所有桩号"""
        stations = []
        for match in self.PATTERNS['station'].finditer(text):
            prefix = match.group(1) or 'K'
            km = int(match.group(2))
            m = int(match.group(3))
            station = km * 1000 + m
            stations.append({
                'raw': match.group(0),
                'prefix': prefix,
                'km': km,
                'm': m,
                'value': station
            })
        return sorted(stations, key=lambda x: x['value'])
    
    def _extract_horizontal(self, text: str, stations: list) -> list:
        """提取平曲线参数"""
        elements = []
        
        # 提取半径
        radii = self.PATTERNS['radius'].findall(text)
        
        # 提取缓和曲线长
        Ls_values = self.PATTERNS['Ls'].findall(text)
        
        # 提取回旋参数
        A_values = self.PATTERNS['A'].findall(text)
        
        # 提取方位角
        azimuths = self.PATTERNS['azimuth'].findall(text)
        
        # 根据桩号生成线元
        for i, station in enumerate(stations):
            elem = {
                "element_type": "直线",
                "start_station": self._format_station(station['value']),
                "end_station": "",
                "azimuth": float(azimuths[0]) if azimuths else 45.0,
                "R": float(radii[0]) if radii else 0,
                "A": float(A_values[0]) if A_values else 0,
                "Ls": float(Ls_values[0]) if Ls_values else 0,
                "x0": 500000 + station['km'] * 100,
                "y0": 3000000 + station['km'] * 100
            }
            
            # 判断曲线类型
            if elem['R'] > 0 and elem['Ls'] > 0:
                elem["element_type"] = "圆曲线"
            elif elem['A'] > 0:
                elem["element_type"] = "缓和曲线"
            
            # 计算终点
            if i < len(stations) - 1:
                end_station = stations[i + 1]['value']
                elem["end_station"] = self._format_station(end_station)
            
            elements.append(elem)
        
        return elements
    
    def _extract_vertical(self, text: str, stations: list) -> list:
        """提取纵曲线参数"""
        elements = []
        
        # 提取坡度
        grades = self.PATTERNS['grade'].findall(text)
        
        # 提取高程
        elevations = self.PATTERNS['elevation'].findall(text)
        
        for i, station in enumerate(stations):
            elem = {
                "station": self._format_station(station['value']),
                "elevation": float(elevations[i]) if i < len(elevations) else 100.0,
                "grade_out": float(grades[0]) if grades else 0,
                "grade_in": float(grades[0]) if grades else 0,
                "length": 0
            }
            
            # 判断是否有竖曲线
            if len(grades) > 1:
                elem["grade_out"] = float(grades[min(i, len(grades)-1)])
                elem["grade_in"] = float(grades[min(i+1, len(grades)-1)])
                elem["length"] = 200  # 默认长度
            
            elements.append(elem)
        
        return elements
    
    def _extract_cross_section(self, text: str) -> Dict:
        """提取横断面参数"""
        cs = {}
        
        # 宽度
        widths = self.PATTERNS['width'].findall(text)
        if widths:
            cs["width"] = float(widths[0])
            cs["lanes"] = int(float(widths[0]) / 3.75 / 2)
        else:
            cs["width"] = 26.0
            cs["lanes"] = 4
        
        cs["crown_slope"] = 2.0
        cs["side_slope"] = 1.5
        cs["superelevation"] = 8.0
        
        return cs
    
    def _validate(self, result: Dict) -> None:
        """验证必要参数"""
        if not result["horizontal"]:
            # 至少需要一个平曲线元素
            result["horizontal"] = [{
                "element_type": "直线",
                "start_station": "K0+000",
                "end_station": "K1+000",
                "azimuth": 45.0,
                "x0": 500000,
                "y0": 3000000
            }]
    
    def _format_station(self, m: float) -> str:
        """格式化桩号"""
        return f"K{int(m)//1000}+{int(m)%1000:03d}"
    
    def to_engine_format(self) -> Dict:
        """
        转换为引擎可用的格式
        
        Returns:
            可以直接传给 NeuralSiteEngine 的字典
        """
        if not self.parsed_data:
            return {}
        
        return {
            "route_id": "PARSED_ROUTE",
            "design_speed": 80,
            "horizontal_alignment": self.parsed_data.get("horizontal", []),
            "vertical_alignment": self.parsed_data.get("vertical", []),
            "cross_section_template": self.parsed_data.get("cross_section", {})
        }


# 测试
if __name__ == "__main__":
    parser = DesignParser()
    
    # 测试文本
    test_texts = [
        "设计说明: 圆曲线半径 R=800米, 缓和曲线长 LS=120米, 交点桩号 K1+500",
        "主线: R=500, LS=80, A=200, 起点 K0+000, 终点 K2+000",
        "变坡点 K0+500, 高程=110m, 坡度 i=20‰, 下一段 i=-15‰"
    ]
    
    for text in test_texts:
        print(f"\nInput: {text}")
        result = parser.parse_text(text)
        print(f"Output: {result}")
