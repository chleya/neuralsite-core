# -*- coding: utf-8 -*-
"""
LOD分层数据模型
支持异形构件的参数化表示 + 分层精度控制
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class LODLevel(Enum):
    """LOD精度级别"""
    LOD0 = 0  # 米级粗精度
    LOD1 = 1  # 分米级中精度
    LOD2 = 2  # 厘米级高精度


class ComponentType(Enum):
    """构件类型"""
    SUBGRADE = "Subgrade"          # 路基
    BRIDGE = "Bridge"              # 桥梁
    TUNNEL = "Tunnel"              # 隧道
    ABnormal_COLUMN = "AbnormalColumn"  # 异形柱
    CULVERT = "Culvert"            # 涵洞
    SLOPE = "Slope"                # 边坡


@dataclass
class Coordinate3D:
    """三维坐标"""
    x: float
    y: float
    z: float
    chainage: Optional[str] = None  # 桩号
    
    def to_dict(self) -> Dict:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "chainage": self.chainage
        }


@dataclass
class LODData:
    """单个LOD级别的数据"""
    level: int
    description: str
    key_points: List[Coordinate3D] = field(default_factory=list)        # LOD0
    boundary_points: List[Coordinate3D] = field(default_factory=list)  # LOD1
    critical_areas: List[Dict] = field(default_factory=list)            # LOD2
    
    def to_dict(self) -> Dict:
        result = {
            "level": self.level,
            "description": self.description
        }
        
        if self.key_points:
            result["keyPoints"] = [p.to_dict() for p in self.key_points]
        
        if self.boundary_points:
            result["boundaryPoints"] = [p.to_dict() for p in self.boundary_points]
        
        if self.critical_areas:
            result["criticalAreas"] = self.critical_areas
            
        return result


@dataclass
class ConstructionInfo:
    """施工信息"""
    fabrication_method: str = ""  # 加工方法
    welding_points: List[Coordinate3D] = field(default_factory=list)
    bolt_holes: List[Dict] = field(default_factory=list)  # {diameter, depth, position}
    
    def to_dict(self) -> Dict:
        return {
            "fabricationMethod": self.fabrication_method,
            "weldingPoints": [p.to_dict() for p in self.welding_points],
            "boltHoles": self.bolt_holes
        }


@dataclass
class Component:
    """工程构件"""
    component_id: str
    component_type: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数化主体
    lod_levels: List[LODData] = field(default_factory=list)
    construction_info: Optional[ConstructionInfo] = None
    
    # 中心线（路线用）
    centerline: List[Coordinate3D] = field(default_factory=list)
    
    def add_lod(self, lod: LODData):
        """添加LOD数据"""
        self.lod_levels.append(lod)
    
    def get_lod(self, level: int) -> Optional[LODData]:
        """获取指定LOD级别数据"""
        for lod in self.lod_levels:
            if lod.level == level:
                return lod
        return None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        result = {
            "componentId": self.component_id,
            "type": self.component_type,
            "description": self.description,
            "parameters": self.parameters,
            "loDLevels": [lod.to_dict() for lod in self.lod_levels]
        }
        
        if self.construction_info:
            result["constructionInfo"] = self.construction_info.to_dict()
            
        if self.centerline:
            result["centerline"] = [c.to_dict() for c in self.centerline]
            
        return result
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class Project:
    """工程项目"""
    project_id: str
    coordinate_system: str = "CGCS2000"  # 坐标系
    components: List[Component] = field(default_factory=list)
    
    def add_component(self, component: Component):
        """添加构件"""
        self.components.append(component)
    
    def get_component(self, component_id: str) -> Optional[Component]:
        """获取构件"""
        for c in self.components:
            if c.component_id == component_id:
                return c
        return None
    
    def to_dict(self) -> Dict:
        return {
            "projectId": self.project_id,
            "coordinateSystem": self.coordinate_system,
            "components": [c.to_dict() for c in self.components]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ========== 工厂函数 ==========

def create_subgrade(component_id: str, start_chainage: str, end_chainage: str, 
                    width: float = 12.0, height: float = 3.0) -> Component:
    """创建路基构件"""
    return Component(
        component_id=component_id,
        component_type=ComponentType.SUBGRADE.value,
        description=f"路基 {start_chainage}-{end_chainage}",
        parameters={
            "width": width,
            "height": height,
            "shape": "梯形"
        }
    )


def create_abnormal_column(component_id: str, width: float, height: float, 
                           total_height: float, slope: float = 0.05,
                           corner_radius: float = 0.1, material: str = "Q345B") -> Component:
    """创建异形柱构件"""
    return Component(
        component_id=component_id,
        component_type=ComponentType.ABnormal_COLUMN.value,
        description="异形钢结构柱",
        parameters={
            "baseShape": "矩形",
            "width": width,
            "height": height,
            "totalHeight": total_height,
            "material": material,
            "slope": slope,
            "cornerRadius": corner_radius
        }
    )


# ========== 测试 ==========

if __name__ == "__main__":
    # 测试：创建异形柱
    column = create_abnormal_column(
        component_id="abnormal-column-001",
        width=0.8,
        height=1.2,
        total_height=3.5,
        slope=0.05,
        corner_radius=0.1,
        material="Q345B"
    )
    
    # 添加LOD0数据（米级）
    column.add_lod(LODData(
        level=0,
        description="粗精度(米级)",
        key_points=[
            Coordinate3D(123.45, 678.90, 0.00),
            Coordinate3D(123.45, 678.90, 3.50)
        ]
    ))
    
    # 添加LOD1数据（分米级）
    column.add_lod(LODData(
        level=1,
        description="中精度(分米级)",
        boundary_points=[
            Coordinate3D(123.45, 678.90, 0.00),
            Coordinate3D(123.65, 678.90, 0.00),
            Coordinate3D(123.65, 679.10, 0.00),
            Coordinate3D(123.45, 679.10, 0.00),
            Coordinate3D(123.45, 678.90, 3.50),
            Coordinate3D(123.65, 678.90, 3.50),
            Coordinate3D(123.65, 679.10, 3.50),
            Coordinate3D(123.45, 679.10, 3.50)
        ]
    ))
    
    # 添加LOD2数据（厘米级）- 关键区域
    column.add_lod(LODData(
        level=2,
        description="高精度(厘米级)",
        critical_areas=[
            {
                "areaName": "顶部连接区",
                "points": [
                    {"x": 123.450, "y": 678.900, "z": 3.450},
                    {"x": 123.455, "y": 678.905, "z": 3.455}
                ]
            },
            {
                "areaName": "底部锚固区", 
                "points": [
                    {"x": 123.450, "y": 678.900, "z": 0.050},
                    {"x": 123.455, "y": 678.905, "z": 0.055}
                ]
            }
        ]
    ))
    
    # 添加施工信息
    column.construction_info = ConstructionInfo(
        fabrication_method="数控切割",
        welding_points=[
            Coordinate3D(123.45, 678.90, 1.0),
            Coordinate3D(123.45, 678.90, 2.0)
        ],
        bolt_holes=[
            {"diameter": 0.02, "depth": 0.1, "position": {"x": 123.45, "y": 678.90, "z": 3.3}},
            {"diameter": 0.02, "depth": 0.1, "position": {"x": 123.65, "y": 678.90, "z": 3.3}}
        ]
    )
    
    print("=== 异形柱构件 ===")
    print(column.to_json())
