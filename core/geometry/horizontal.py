# -*- coding: utf-8 -*-
"""
平曲线计算模块
基于JTG D20-2017规范
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class Point2D:
    """二维点"""
    x: float
    y: float


@dataclass
class Point3D:
    """三维点"""
    x: float
    y: float
    z: float = 0.0


class HorizontalCurveElement:
    """平曲线线元基类"""
    
    def __init__(self, start_station: float, end_station: float):
        self.start_station = start_station  # 起点桩号(m)
        self.end_station = end_station        # 终点桩号(m)
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        """获取坐标 (x, y, azimuth)
        
        Args:
            station: 桩号(m)
            
        Returns:
            (x, y, azimuth)
        """
        raise NotImplementedError
    
    @property
    def length(self) -> float:
        """线元长度"""
        return self.end_station - self.start_station


class LineElement(HorizontalCurveElement):
    """直线线元
    
    公式:
    x = x0 + l * cos(α)
    y = y0 + l * sin(α)
    """
    
    def __init__(self, start_station: float, end_station: float,
                 azimuth: float, x0: float, y0: float):
        super().__init__(start_station, end_station)
        self.azimuth = azimuth  # 方位角(度)
        self.x0 = x0           # 起点X
        self.y0 = y0           # 起点Y
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        l = station - self.start_station
        rad = math.radians(self.azimuth)
        
        x = self.x0 + l * math.cos(rad)
        y = self.y0 + l * math.sin(rad)
        
        return x, y, self.azimuth
    
    def get_point_at_distance(self, distance: float) -> Point2D:
        """获取距离起点指定距离的点"""
        rad = math.radians(self.azimuth)
        return Point2D(
            x=self.x0 + distance * math.cos(rad),
            y=self.y0 + distance * math.sin(rad)
        )


class CircularCurveElement(HorizontalCurveElement):
    """圆曲线线元
    
    公式:
    x = R * sin(θ)
    y = R * (1 - cos(θ))
    θ = l / R
    """
    
    def __init__(self, start_station: float, end_station: float,
                 radius: float, azimuth: float, x0: float, y0: float,
                 center_x: float = None, center_y: float = None,
                 direction: str = "右"):
        super().__init__(start_station, end_station)
        self.radius = radius          # 半径(m)
        self.azimuth = azimuth        # 起点切线方位角(度)
        self.x0 = x0                  # 起点X
        self.y0 = y0                  # 起点Y
        self.center_x = center_x      # 圆心X
        self.center_y = center_y      # 圆心Y
        self.direction = direction    # 转向: 左/右
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        l = station - self.start_station
        theta = l / self.radius  # 圆心角
        
        # 起点切线方位角
        start_rad = math.radians(self.azimuth)
        
        # 局部坐标 (以起点为原点，切线方向为X轴)
        local_x = self.radius * math.sin(theta)
        local_y = self.radius * (1 - math.cos(theta))
        
        # 旋转到真实坐标系
        if self.direction == "右":
            x = self.x0 + local_x * math.cos(start_rad) - local_y * math.sin(start_rad)
            y = self.y0 + local_x * math.sin(start_rad) + local_y * math.cos(start_rad)
        else:
            x = self.x0 + local_x * math.cos(start_rad) + local_y * math.sin(start_rad)
            y = self.y0 + local_x * math.sin(start_rad) - local_y * math.cos(start_rad)
        
        # 当前方位角
        direction_sign = 1 if self.direction == "右" else -1
        current_azimuth = self.azimuth + math.degrees(theta) * direction_sign
        
        return x, y, current_azimuth
    
    @property
    def central_angle(self) -> float:
        """圆心角(度)"""
        return math.degrees(self.length / self.radius)
    
    @property
    def chord(self) -> float:
        """弦长"""
        return 2 * self.radius * math.sin(math.radians(self.central_angle) / 2)
    
    @property
    def tangent_length(self) -> float:
        """切线长"""
        return self.radius * math.tan(math.radians(self.central_angle) / 2)
    
    @property
    def external_distance(self) -> float:
        """外矢距"""
        return self.radius * (1 / math.cos(math.radians(self.central_angle) / 2) - 1)


class SpiralCurveElement(HorizontalCurveElement):
    """缓和曲线线元 (三次回旋线)
    
    公式:
    x = l - l^5/(40*R^2*Ls^2) + l^9/(3456*R^4*Ls^4)
    y = l^3/(6*R*Ls) - l^7/(336*R^3*Ls^3) + l^11/(42240*R^5*Ls^5)
    """
    
    def __init__(self, start_station: float, end_station: float,
                 azimuth: float, x0: float, y0: float,
                 A: float, radius: float = None, direction: str = "右"):
        super().__init__(start_station, end_station)
        self.azimuth = azimuth    # 起点切线方位角
        self.x0 = x0            # 起点X
        self.y0 = y0            # 起点Y
        self.A = A              # 回旋参数
        self.radius = radius    # 圆曲线半径(缓和曲线终点)
        self.direction = direction  # 转向: 左/右
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        l = station - self.start_station  # 局部里程
        
        if self.A == 0:
            return self.x0, self.y0, self.azimuth
        
        # 参数tau
        tau = l * l / (2 * self.A * self.A)
        
        # 级数展开 (取前3项)
        x = l * (1 - tau**2/10 + tau**4/216)
        y = l * l * l / (6 * self.A * self.A) * (1 - tau**2/42 + tau**4/1320)
        
        # 方向判断
        sign = 1 if self.direction == "右" else -1
        
        # 旋转到真实坐标系
        rad = math.radians(self.azimuth)
        rx = x * math.cos(rad) - sign * y * math.sin(rad)
        ry = x * math.sin(rad) + sign * y * math.cos(rad)
        
        # 当前方位角
        if self.radius:
            azimuth_change = math.degrees(l / self.A * self.A / self.radius) * sign
        else:
            azimuth_change = 0
        
        return self.x0 + rx, self.y0 + ry, self.azimuth + azimuth_change
    
    @property
    def length(self) -> float:
        """缓和曲线长度"""
        return self.end_station - self.start_station
    
    @property
    def parameter_A(self) -> float:
        """回旋参数A"""
        return self.A


class HorizontalAlignment:
    """平曲线组合"""
    
    def __init__(self):
        self.elements = []
    
    def add_element(self, element: HorizontalCurveElement):
        """添加线元"""
        self.elements.append(element)
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        """获取任意桩号坐标"""
        for elem in self.elements:
            if elem.start_station <= station <= elem.end_station:
                return elem.get_coordinate(station)
        
        # 外推
        if station < self.elements[0].start_station:
            elem = self.elements[0]
            ds = station - elem.start_station
            return self._extrapolate(elem, ds, forward=False)
        else:
            elem = self.elements[-1]
            ds = station - elem.start_station
            return self._extrapolate(elem, ds, forward=True)
    
    def _extrapolate(self, elem, ds: float, forward: bool) -> Tuple[float, float, float]:
        """外推"""
        rad = math.radians(elem.azimuth)
        
        if forward:
            x = elem.x0 + ds * math.cos(rad)
            y = elem.y0 + ds * math.sin(rad)
        else:
            x = elem.x0 - ds * math.cos(rad)
            y = elem.y0 - ds * math.sin(rad)
        
        return x, y, elem.azimuth
    
    @property
    def start_station(self) -> float:
        """起点桩号"""
        return self.elements[0].start_station if self.elements else 0
    
    @property
    def end_station(self) -> float:
        """终点桩号"""
        return self.elements[-1].end_station if self.elements else 0
    
    @property
    def total_length(self) -> float:
        """总长度"""
        return self.end_station - self.start_station


# 测试
if __name__ == "__main__":
    # 创建平曲线组合
    h = HorizontalAlignment()
    
    # 直线
    h.add_element(LineElement(0, 500, 45, 500000, 3000000))
    
    # 缓和曲线
    h.add_element(SpiralCurveElement(500, 600, 45, 500353.553, 3000353.553, 300, 800, "右"))
    
    # 圆曲线
    h.add_element(CircularCurveElement(600, 1200, 800, 45, 500424.264, 3000424.264, 
                                        500424.264, 3000224.264, "右"))
    
    # 测试
    print("=== Horizontal Curve Test ===")
    for s in [0, 250, 500, 600, 800, 1000, 1200]:
        x, y, az = h.get_coordinate(s)
        print(f"K{s//1000}+{s%1000:03d}: X={x:.3f} Y={y:.3f} Az={az:.3f}°")
