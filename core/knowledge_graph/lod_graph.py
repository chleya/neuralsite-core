# -*- coding: utf-8 -*-
"""
LOD数据与Neo4j图数据库的映射
"""

from typing import Dict, List, Optional
import sys
sys.path.insert(0, '.')

from core.models.lod import Component, Project, LODLevel, Coordinate3D
from storage.graph_db import get_graph_db


def save_component_to_graph(component: Component, project_id: str) -> bool:
    """将构件保存到图数据库"""
    db = get_graph_db()
    
    if not db.driver:
        print("Neo4j not available")
        return False
    
    # 创建构件节点
    db.merge_node("Component", "id", component.component_id, {
        "id": component.component_id,
        "type": component.component_type,
        "description": component.description,
        "parameters": str(component.parameters)
    })
    
    # 建立项目-构件关系
    db.create_relationship(
        "Project", "id", project_id,
        "CONTAINS",
        "Component", "id", component.component_id
    )
    
    # 保存中心线点
    for i, point in enumerate(component.centerline):
        coord_id = f"{component.component_id}_centerline_{i}"
        db.merge_node("CenterlinePoint", "id", coord_id, {
            "id": coord_id,
            "x": point.x,
            "y": point.y,
            "z": point.z,
            "chainage": point.chainage
        })
        
        # 关联到构件
        db.create_relationship(
            "Component", "id", component.component_id,
            "HAS_CENTERLINE",
            "CenterlinePoint", "id", coord_id
        )
    
    # 保存LOD数据
    for lod in component.lod_levels:
        section_id = f"{component.component_id}_LOD{lod.level}"
        
        db.merge_node("Section", "id", section_id, {
            "id": section_id,
            "lod": lod.level,
            "description": lod.description
        })
        
        # 构件-段落关系
        db.create_relationship(
            "Component", "id", component.component_id,
            "HAS_SECTION",
            "Section", "id", section_id
        )
        
        # LOD0: 关键点
        if lod.level == 0 and lod.key_points:
            for i, point in enumerate(lod.key_points):
                point_id = f"{section_id}_key_{i}"
                db.merge_node("KeyPoint", "id", point_id, {
                    "id": point_id,
                    "x": point.x,
                    "y": point.y,
                    "z": point.z
                })
                db.create_relationship(
                    "Section", "id", section_id,
                    "HAS_KEYPOINTS",
                    "KeyPoint", "id", point_id
                )
        
        # LOD1: 边界点
        if lod.level == 1 and lod.boundary_points:
            for i, point in enumerate(lod.boundary_points):
                point_id = f"{section_id}_boundary_{i}"
                db.merge_node("BoundaryPoint", "id", point_id, {
                    "id": point_id,
                    "x": point.x,
                    "y": point.y,
                    "z": point.z
                })
                db.create_relationship(
                    "Section", "id", section_id,
                    "HAS_BOUNDARY",
                    "BoundaryPoint", "id", point_id
                )
        
        # LOD2: 关键区域高精度点
        if lod.level == 2 and lod.critical_areas:
            for area in lod.critical_areas:
                area_name = area.get("areaName", "unknown")
                area_id = f"{section_id}_{area_name}"
                
                db.merge_node("CriticalArea", "id", area_id, {
                    "id": area_id,
                    "name": area_name
                })
                
                db.create_relationship(
                    "Section", "id", section_id,
                    "HAS_CRITICAL_AREA",
                    "CriticalArea", "id", area_id
                )
                
                # 高精度点
                for j, point in enumerate(area.get("points", [])):
                    hp_id = f"{area_id}_hp_{j}"
                    db.merge_node("HighPrecisionPoint", "id", hp_id, {
                        "id": hp_id,
                        "x": point.get("x", 0),
                        "y": point.get("y", 0),
                        "z": point.get("z", 0)
                    })
                    db.create_relationship(
                        "CriticalArea", "id", area_id,
                        "HAS_POINTS",
                        "HighPrecisionPoint", "id", hp_id
                    )
    
    # 施工信息
    if component.construction_info:
        ci = component.construction_info
        
        # 焊接点
        for i, wp in enumerate(ci.welding_points):
            wp_id = f"{component.component_id}_weld_{i}"
            db.merge_node("WeldingPoint", "id", wp_id, {
                "id": wp_id,
                "x": wp.x,
                "y": wp.y,
                "z": wp.z
            })
            db.create_relationship(
                "Component", "id", component.component_id,
                "HAS_WELDING",
                "WeldingPoint", "id", wp_id
            )
        
        # 螺栓孔
        for i, bh in enumerate(ci.bolt_holes):
            bh_id = f"{component.component_id}_bolt_{i}"
            pos = bh.get("position", {})
            db.merge_node("BoltHole", "id", bh_id, {
                "id": bh_id,
                "diameter": bh.get("diameter", 0),
                "depth": bh.get("depth", 0),
                "x": pos.get("x", 0),
                "y": pos.get("y", 0),
                "z": pos.get("z", 0)
            })
            db.create_relationship(
                "Component", "id", component.component_id,
                "HAS_BOLT",
                "BoltHole", "id", bh_id
            )
    
    return True


def query_high_precision_points(component_id: str, chainage: str = None) -> List[Dict]:
    """查询高精度点"""
    db = get_graph_db()
    
    if not db.driver:
        return []
    
    query = """
    MATCH (c:Component {id: $component_id})-[:HAS_SECTION]->(s:Section {lod: 2})
    MATCH (s)-[:HAS_CRITICAL_AREA]->(area:CriticalArea)
    MATCH (area)-[:HAS_POINTS]->(p:HighPrecisionPoint)
    RETURN area.name as areaName, p.x, p.y, p.z
    """
    
    return db.execute_query(query, {"component_id": component_id})


def init_lod_schema():
    """初始化LOD图结构"""
    db = get_graph_db()
    
    if not db.driver:
        return False
    
    # 约束
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:HighPrecisionPoint) REQUIRE p.id IS UNIQUE",
    ]
    
    # 索引
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (c:Component) ON (c.type)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Section) ON (s.lod)",
    ]
    
    for c in constraints:
        db.execute_write(c)
    
    for i in indexes:
        db.execute_write(i)
    
    return True


if __name__ == "__main__":
    # 测试
    from core.models.lod import create_abnormal_column, LODData, Coordinate3D, ConstructionInfo
    
    # 创建异形柱
    column = create_abnormal_column(
        component_id="abnormal-column-001",
        width=0.8,
        height=1.2,
        total_height=3.5
    )
    
    # 添加LOD数据
    column.add_lod(LODData(
        level=0,
        description="粗精度",
        key_points=[
            Coordinate3D(123.45, 678.90, 0.00),
            Coordinate3D(123.45, 678.90, 3.50)
        ]
    ))
    
    # 尝试保存
    init_lod_schema()
    save_component_to_graph(column, "NS-001")
    
    print("LOD数据已保存到Neo4j")
