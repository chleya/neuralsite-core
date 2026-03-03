# -*- coding: utf-8 -*-
"""
3D模型生成器
"""

import os
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Vertex:
    """顶点"""
    x: float
    y: float
    z: float


@dataclass
class Face:
    """面"""
    v1: int
    v2: int
    v3: int


class ModelGenerator:
    """
    3D模型生成器
    
    生成OBJ格式的三维模型
    """
    
    def __init__(self):
        self.vertices = []
        self.faces = []
    
    def add_vertex(self, x: float, y: float, z: float) -> int:
        """添加顶点，返回索引"""
        self.vertices.append(Vertex(x, y, z))
        return len(self.vertices)
    
    def add_face(self, v1: int, v2: int, v3: int):
        """添加面"""
        self.faces.append(Face(v1, v2, v3))
    
    def generate_mesh(self, coords: List[Dict], width: float = 10) -> None:
        """
        生成道路网格
        
        Args:
            coords: 路线坐标列表 [{"x", "y", "z", "azimuth"}, ...]
            width: 道路宽度
        """
        import math
        
        half_width = width / 2
        
        for i, coord in enumerate(coords):
            x = coord['x']
            y = coord['y']
            z = coord['z']
            azimuth = coord.get('azimuth', 0)
            
            # 计算左右点
            rad = math.radians(azimuth)
            
            # 左侧点
            left_x = x + half_width * math.cos(rad + math.pi/2)
            left_y = y + half_width * math.sin(rad + math.pi/2)
            left_z = z
            
            # 右侧点
            right_x = x + half_width * math.cos(rad - math.pi/2)
            right_y = y + half_width * math.sin(rad - math.pi/2)
            right_z = z
            
            # 添加顶点
            left_idx = self.add_vertex(left_x, left_y, left_z)
            center_idx = self.add_vertex(x, y, z)
            right_idx = self.add_vertex(right_x, right_y, right_z)
            
            # 添加面（下一段）
            if i > 0:
                # 找到之前的顶点索引
                prev_left = (i - 1) * 3 + 1
                prev_center = prev_left + 1
                prev_right = prev_left + 2
                
                # 左边三角形
                self.add_face(prev_left, prev_center, left_idx)
                # 右边三角形
                self.add_face(prev_center, prev_right, right_idx)
    
    def generate_terrain_mesh(self, coords: List[Dict], interval: float = 5) -> None:
        """
        生成带横断面的地形网格
        
        Args:
            coords: 路线坐标
            interval: 横断面的间隔
        """
        # 为每个坐标点生成完整的横断面
        for i, coord in enumerate(coords):
            x = coord['x']
            y = coord['y']
            z = coord['z']
            
            # 这里可以调用横断面子生成器
            # 简化版本：只生成中心线
    
    def to_obj(self) -> str:
        """
        导出为OBJ格式
        
        Returns:
            OBJ格式字符串
        """
        lines = []
        
        # 顶点
        for v in self.vertices:
            lines.append(f"v {v.x:.6f} {v.y:.6f} {v.z:.6f}")
        
        # 面
        for f in self.faces:
            lines.append(f"f {f.v1} {f.v2} {f.v3}")
        
        return "\n".join(lines)
    
    def save_obj(self, filepath: str) -> None:
        """保存为OBJ文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_obj())
        print(f"模型已保存: {filepath}")
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "vertices": [(v.x, v.y, v.z) for v in self.vertices],
            "faces": [(f.v1, f.v2, f.v3) for f in self.faces],
            "vertex_count": len(self.vertices),
            "face_count": len(self.faces)
        }


class CrossSectionGenerator:
    """
    横断面生成器
    """
    
    def __init__(self, width: float = 26):
        self.width = width
    
    def generate(self, x: float, y: float, z: float, azimuth: float) -> List[Tuple[float, float, float]]:
        """
        生成横断面点
        
        Returns:
            [(x, y, z), ...] 从左到右的点
        """
        import math
        
        half = self.width / 2
        rad = math.radians(azimuth)
        
        points = []
        
        # 左侧路边
        left_x = x + half * math.cos(rad + math.pi/2)
        left_y = y + half * math.sin(rad + math.pi/2)
        points.append((left_x, left_y, z))
        
        # 中心
        points.append((x, y, z))
        
        # 右侧路边
        right_x = x + half * math.cos(rad - math.pi/2)
        right_y = y + half * math.sin(rad - math.pi/2)
        points.append((right_x, right_y, z))
        
        return points


class EarthworkCalculator:
    """
    土方量计算器
    """
    
    def __init__(self):
        self.cross_sections = []
    
    def add_section(self, station: float, area: float):
        """添加横断面面积"""
        self.cross_sections.append({"station": station, "area": area})
    
    def calculate_volume(self) -> Dict:
        """
        计算土方量（平均断面法）
        
        Returns:
            {"fill": 填方, "cut": 挖方, "total": 总计}
        """
        if len(self.cross_sections) < 2:
            return {"fill": 0, "cut": 0, "total": 0}
        
        volume = 0
        
        for i in range(len(self.cross_sections) - 1):
            s1 = self.cross_sections[i]
            s2 = self.cross_sections[i + 1]
            
            # 间距
            distance = s2['station'] - s1['station']
            
            # 平均面积
            avg_area = (s1['area'] + s2['area']) / 2
            
            # 体积
            volume += avg_area * distance
        
        return {
            "fill": max(0, volume),
            "cut": max(0, -volume),
            "total": abs(volume)
        }
    
    def calculate_area(self, width: float, depth: float = 0) -> float:
        """计算简单断面面积"""
        # 简化：矩形断面
        return width * depth if depth > 0 else 0


# 测试
if __name__ == "__main__":
    # 测试模型生成
    gen = ModelGenerator()
    
    # 添加测试坐标
    test_coords = [
        {"x": 500000, "y": 3000000, "z": 100, "azimuth": 45},
        {"x": 500100, "y": 3000070, "z": 102, "azimuth": 45},
        {"x": 500200, "y": 3000141, "z": 104, "azimuth": 45},
    ]
    
    gen.generate_mesh(test_coords, width=10)
    
    print("=== Model Generator Test ===")
    print(f"Vertices: {len(gen.vertices)}")
    print(f"Faces: {len(gen.faces)}")
    
    # 保存OBJ
    obj_path = "test_model.obj"
    gen.save_obj(obj_path)
    
    # 测试土方计算
    calc = EarthworkCalculator()
    calc.add_section(0, 100)
    calc.add_section(100, 120)
    calc.add_section(200, 110)
    
    volume = calc.calculate_volume()
    print(f"\n=== Earthwork Test ===")
    print(f"Volume: {volume}")
