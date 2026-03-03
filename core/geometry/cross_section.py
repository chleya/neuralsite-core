# -*- coding: utf-8 -*-
"""
横断面计算模块
基于JTG D20-2017规范
"""

import math
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class CrossSectionTemplate:
    """横断面模板"""
    width: float = 26.0          # 路基宽度(m)
    lane_width: float = 3.75    # 车道宽度(m)
    lanes: int = 4               # 车道数
    crown_slope: float = 2.0     # 路拱坡(%)
    side_slope: float = 1.5      # 边坡坡率 (1:m)
    ditch_depth: float = 0.8     # 排水沟深度(m)
    ditch_width: float = 0.5     # 排水沟宽度(m)
    shoulder_width: float = 2.5  # 硬路肩宽度(m)
    verge_width: float = 0.75    # 土路肩宽度(m)


@dataclass
class SuperElevation:
    """超高设置"""
    max_rate: float = 8.0         # 最大超高(%)
    rotation_axis: str = "中"     # 旋转轴: 中/内/外
    transition_type: str = "线性"  # 渐变方式


@dataclass
class Widening:
    """加宽设置"""
    max_width: float = 0.8        # 最大加宽值(m)
    transition_length: float = 0  # 渐变长度(m)


class CrossSectionCalculator:
    """横断面计算器"""
    
    def __init__(self, template: CrossSectionTemplate = None):
        self.template = template or CrossSectionTemplate()
        self.super_elevation = SuperElevation()
        self.widening = Widening()
    
    def calculate(self, station: float, offset: float = 0, 
                  super_rate: float = 0, widening_value: float = 0) -> Dict:
        """计算横断面
        
        Args:
            station: 桩号(m)
            offset: 横向偏移(m), 左负右正
            super_rate: 超高值(%)
            widening_value: 加宽值(m)
            
        Returns:
            断面点坐标 {center, left, right, points}
        """
        half_width = self.template.width / 2 + widening_value
        
        # 路拱高差
        crown_rise = half_width * self.template.crown_slope / 100
        
        # 超高旋转
        if self.super_elevation.rotation_axis == "中":
            # 绕中心旋转
            left_z_offset = -half_width * super_rate / 100
            right_z_offset = half_width * super_rate / 100
        elif self.super_elevation.rotation_axis == "内":
            # 绕内侧旋转
            left_z_offset = -self.template.width * super_rate / 100
            right_z_offset = 0
        else:
            # 绕外侧旋转
            left_z_offset = 0
            right_z_offset = self.template.width * super_rate / 100
        
        # 应用偏移
        left_offset = -(half_width + offset)
        right_offset = half_width - offset
        
        # 计算点
        return {
            "station": station,
            "offset": offset,
            "half_width": half_width,
            "crown_rise": crown_rise,
            "super_rate": super_rate,
            "widening": widening_value,
            "left_offset": left_offset,
            "right_offset": right_offset,
            "left_z_offset": left_z_offset,
            "right_z_offset": right_z_offset
        }
    
    def get_section_points(self, center_x: float, center_y: float, center_z: float,
                          azimuth: float, station: float, offset: float = 0,
                          super_rate: float = 0, widening_value: float = 0) -> Dict:
        """获取断面各点坐标
        
        Returns:
            {center, left_edge, right_edge, left_ditch, right_ditch}
        """
        cs = self.calculate(station, offset, super_rate, widening_value)
        
        rad = math.radians(azimuth)
        
        # 中心点
        center = (center_x, center_y, center_z)
        
        # 左侧边缘点
        left_x = center_x + cs['left_offset'] * math.cos(rad + math.pi/2)
        left_y = center_y + cs['left_offset'] * math.sin(rad + math.pi/2)
        left_z = center_z + cs['crown_rise'] + cs['left_z_offset']
        left_edge = (left_x, left_y, left_z)
        
        # 右侧边缘点
        right_x = center_x + cs['right_offset'] * math.cos(rad - math.pi/2)
        right_y = center_y + cs['right_offset'] * math.sin(rad - math.pi/2)
        right_z = center_z - cs['crown_rise'] + cs['right_z_offset']
        right_edge = (right_x, right_y, right_z)
        
        # 左侧排水沟
        left_ditch_x = left_x - self.template.ditch_width * math.cos(rad + math.pi/2)
        left_ditch_y = left_y - self.template.ditch_width * math.sin(rad + math.pi/2)
        left_ditch_z = left_z - self.template.ditch_depth
        left_ditch = (left_ditch_x, left_ditch_y, left_ditch_z)
        
        # 右侧排水沟
        right_ditch_x = right_x + self.template.ditch_width * math.cos(rad - math.pi/2)
        right_ditch_y = right_y + self.template.ditch_width * math.sin(rad - math.pi/2)
        right_ditch_z = right_z - self.template.ditch_depth
        right_ditch = (right_ditch_x, right_ditch_y, right_ditch_z)
        
        return {
            "center": center,
            "left_edge": left_edge,
            "right_edge": right_edge,
            "left_ditch": left_ditch,
            "right_ditch": right_ditch
        }
    
    def get_super_elevation_rate(self, radius: float, design_speed: int) -> float:
        """计算超高值
        
        Args:
            radius: 圆曲线半径(m)
            design_speed: 设计速度(km/h)
            
        Returns:
            超高值(%)
        """
        if radius <= 0:
            return 0
        
        # 规范公式: e = V^2 / (127R) - f
        # 简化: 超高 = V^2 / (15R)
        rate = design_speed ** 2 / (15 * radius)
        
        # 限制最大值
        max_rate = self.super_elevation.max_rate
        return min(rate, max_rate)


class CrossSectionBuilder:
    """横断面构建器"""
    
    def __init__(self, template: CrossSectionTemplate = None):
        self.template = template or CrossSectionTemplate()
    
    def build_polygon(self, center_x: float, center_y: float, center_z: float,
                      azimuth: float, super_rate: float = 0) -> List[Tuple[float, float, float]]:
        """构建横断面的多边形点(用于可视化)
        
        Returns:
            [(x,y,z), ...] 顺序: 左侧路肩->左侧边缘->路拱->右侧边缘->右侧路肩
        """
        half = self.template.width / 2
        shoulder = self.template.shoulder_width
        lane = self.template.lane_width * self.template.lanes / 2
        
        rad = math.radians(azimuth)
        
        # 路拱高差
        crown = half * self.template.crown_slope / 100
        
        # 点序列 (从左到右)
        points = []
        
        # 左侧土路肩外缘
        x = center_x - half * math.cos(rad + math.pi/2)
        y = center_y - half * math.sin(rad + math.pi/2)
        z = center_z + crown + (half - shoulder) * self.template.side_slope
        points.append((x, y, z))
        
        # 左侧硬路肩
        x = center_x - (half - shoulder) * math.cos(rad + math.pi/2)
        y = center_y - (half - shoulder) * math.sin(rad + math.pi/2)
        z = center_z + crown + super_rate * (half - shoulder) / 100
        points.append((x, y, z))
        
        # 左侧路缘带边缘
        x = center_x - lane * math.cos(rad + math.pi/2)
        y = center_y - lane * math.sin(rad + math.pi/2)
        z = center_z + crown * lane / half + super_rate * lane / 100
        points.append((x, y, z))
        
        # 中心点
        points.append((center_x, center_y, center_z))
        
        # 右侧路缘带边缘
        x = center_x + lane * math.cos(rad - math.pi/2)
        y = center_y + lane * math.sin(rad - math.pi/2)
        z = center_z + crown * lane / half - super_rate * lane / 100
        points.append((x, y, z))
        
        # 右侧硬路肩
        x = center_x + (half - shoulder) * math.cos(rad - math.pi/2)
        y = center_y + (half - shoulder) * math.sin(rad - math.pi/2)
        z = center_z + crown - super_rate * (half - shoulder) / 100
        points.append((x, y, z))
        
        # 右侧土路肩外缘
        x = center_x + half * math.cos(rad - math.pi/2)
        y = center_y + half * math.sin(rad - math.pi/2)
        z = center_z + crown + (half - shoulder) * self.template.side_slope
        points.append((x, y, z))
        
        return points


# 测试
if __name__ == "__main__":
    cs_calc = CrossSectionCalculator()
    
    print("=== Cross Section Test ===")
    
    # 计算超高
    rate = cs_calc.get_super_elevation_rate(800, 80)
    print(f"Super elevation at R=800m, V=80km/h: {rate:.2f}%")
    
    # 断面点
    points = cs_calc.get_section_points(
        500000, 3000000, 100, 45, 500, 0, rate, 0
    )
    
    print(f"\nSection at K0+500:")
    print(f"Center: ({points['center'][0]:.3f}, {points['center'][1]:.3f}, {points['center'][2]:.3f})")
    print(f"Left Edge: ({points['left_edge'][0]:.3f}, {points['left_edge'][1]:.3f}, {points['left_edge'][2]:.3f})")
    print(f"Right Edge: ({points['right_edge'][0]:.3f}, {points['right_edge'][1]:.3f}, {points['right_edge'][2]:.3f})")
