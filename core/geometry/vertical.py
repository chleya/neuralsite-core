# -*- coding: utf-8 -*-
"""
竖曲线计算模块
基于JTG D20-2017规范
"""

import math
from typing import Optional
from dataclasses import dataclass


@dataclass
class VerticalCurveElement:
    """竖曲线线元"""
    station: float           # 变坡点桩号(m)
    elevation: float        # 变坡点高程(m)
    grade_in: float = 0     # 入口坡度(‰)
    grade_out: float = 0    # 出口坡度(‰)
    length: float = 0       # 竖曲线长度(m)
    curve_type: str = "凸"   # 曲线类型: 凸/凹


class VerticalAlignment:
    """纵曲线组合"""
    
    def __init__(self):
        self.elements = []
    
    def add_element(self, element: VerticalCurveElement):
        """添加变坡点"""
        self.elements.append(element)
    
    def get_elevation(self, station: float) -> float:
        """获取任意桩号高程
        
        Args:
            station: 桩号(m)
            
        Returns:
            高程(m)
        """
        if not self.elements:
            return 0
        
        # 找所在坡段
        for i in range(len(self.elements) - 1):
            p1 = self.elements[i]
            p2 = self.elements[i + 1]
            
            if p1.station <= station <= p2.station:
                return self._calculate_in_segment(p1, p2, station)
        
        # 外推
        if station < self.elements[0].station:
            p = self.elements[0]
            ds = station - p.station
            return p.elevation + ds * p.grade_out / 1000
        else:
            p = self.elements[-1]
            ds = station - p.station
            return p.elevation + ds * p.grade_in / 1000
    
    def _calculate_in_segment(self, p1: VerticalCurveElement, p2: VerticalCurveElement, 
                               station: float) -> float:
        """在坡段内计算"""
        l = station - p1.station  # 距变坡点距离
        length = p2.station - p1.station  # 坡段长度
        
        # 无竖曲线
        if p1.length == 0 or l <= 0:
            return p1.elevation + l * p1.grade_out / 1000
        
        # 有竖曲线 - 抛物线公式
        if l <= p1.length:
            # 竖曲线段
            # z = z_vp + i1*x + (i2-i1)*x^2/(2L)
            grade_diff = p1.grade_out - p1.grade_in  # ‰
            z = (p1.elevation + 
                 p1.grade_in * l / 1000 + 
                 grade_diff * l * l / (2 * p1.length * 1000))
            return z
        elif l <= length:
            # 超出竖曲线段
            l2 = l - p1.length
            z = (p1.elevation + 
                 p1.grade_out * p1.length / 1000 + 
                 p1.grade_out * l2 / 1000)
            return z
        else:
            # 超出坡段
            return p2.elevation
    
    @property
    def start_station(self) -> float:
        """起点桩号"""
        return self.elements[0].station if self.elements else 0
    
    @property
    def end_station(self) -> float:
        """终点桩号"""
        return self.elements[-1].station if self.elements else 0
    
    @property
    def total_length(self) -> float:
        """总长度"""
        return self.end_station - self.start_station
    
    def get_grade_at(self, station: float) -> float:
        """获取任意桩号的坡度(‰)"""
        if not self.elements:
            return 0
        
        for i in range(len(self.elements) - 1):
            p1 = self.elements[i]
            p2 = self.elements[i + 1]
            
            if p1.station <= station <= p2.station:
                l = station - p1.station
                
                # 在竖曲线内
                if p1.length > 0 and l <= p1.length:
                    grade_diff = p1.grade_out - p1.grade_in
                    return p1.grade_in + grade_diff * l / p1.length
                # 在直坡段
                return p1.grade_out
        
        # 外推
        if station < self.elements[0].station:
            return self.elements[0].grade_out
        return self.elements[-1].grade_in


class GradeSection:
    """坡段(无竖曲线)"""
    
    def __init__(self, start_station: float, end_station: float,
                 start_elevation: float, grade: float):
        self.start_station = start_station
        self.end_station = end_station
        self.start_elevation = start_elevation
        self.grade = grade  # ‰
    
    def get_elevation(self, station: float) -> float:
        """获取高程"""
        l = station - self.start_station
        return self.start_elevation + l * self.grade / 1000


# 测试
if __name__ == "__main__":
    # 创建纵曲线
    v = VerticalAlignment()
    
    # 变坡点1
    v.add_element(VerticalCurveElement(0, 100.0, grade_out=20))
    
    # 变坡点2 (有竖曲线)
    v.add_element(VerticalCurveElement(500, 110.0, grade_in=20, grade_out=-15, 
                                        length=200, curve_type="凸"))
    
    # 变坡点3
    v.add_element(VerticalCurveElement(1200, 99.5, grade_in=-15, grade_out=10,
                                        length=150, curve_type="凹"))
    
    # 变坡点4
    v.add_element(VerticalCurveElement(2000, 108.0, grade_in=10))
    
    # 测试
    print("=== Vertical Curve Test ===")
    for s in [0, 100, 250, 400, 500, 600, 800, 1000, 1200, 1500, 2000]:
        z = v.get_elevation(s)
        grade = v.get_grade_at(s)
        print(f"K{s//1000}+{s%1000:03d}: Z={z:.3f}m Grade={grade:.2f}‰")
