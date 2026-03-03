# -*- coding: utf-8 -*-
"""
图数据Schema定义
"""

from storage.graph_db import get_graph_db, GraphDatabase


def init_schema():
    """初始化图数据库结构"""
    db = get_graph_db()
    
    if not db.driver:
        print("Neo4j not available, skip schema init")
        return False
    
    # 创建约束
    constraints = [
        # 项目唯一ID
        "CREATE CONSTRAINT IF NOT EXISTS project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        # 图纸唯一ID
        "CREATE CONSTRAINT IF NOT EXISTS drawing_id IF NOT EXISTS FOR (d:Drawing) REQUIRE d.id IS UNIQUE",
        # 特征唯一ID
        "CREATE CONSTRAINT IF NOT EXISTS feature_id IF NOT EXISTS FOR (f:Feature) REQUIRE f.id IS UNIQUE",
        # 坐标唯一ID
        "CREATE CONSTRAINT IF NOT EXISTS coord_id IF NOT EXISTS FOR (c:Coordinate) REQUIRE c.id IS UNIQUE",
    ]
    
    # 创建索引
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (f:Feature) ON (f.chainage)",
        "CREATE INDEX IF NOT EXISTS FOR (c:Coordinate) ON (c.chainage)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Project) ON (p.name)",
    ]
    
    # 执行
    for c in constraints:
        try:
            db.execute_write(c)
            print(f"Constraint: {c[:50]}...")
        except Exception as e:
            print(f"Constraint error: {e}")
    
    for i in indexes:
        try:
            db.execute_write(i)
            print(f"Index: {i[:50]}...")
        except Exception as e:
            print(f"Index error: {e}")
    
    print("Schema init complete")
    return True


def create_project(name: str, description: str = "") -> bool:
    """创建项目节点"""
    db = get_graph_db()
    return db.merge_node("Project", "name", name, {
        "name": name,
        "description": description
    })


def create_drawing(project_name: str, drawing_name: str, drawing_type: str) -> bool:
    """创建图纸节点"""
    db = get_graph_db()
    
    # 创建图纸
    db.merge_node("Drawing", "name", drawing_name, {
        "name": drawing_name,
        "type": drawing_type
    })
    
    # 建立关系
    return db.create_relationship(
        "Project", "name", project_name,
        "HAS_DRAWING",
        "Drawing", "name", drawing_name
    )


def create_feature(drawing_name: str, feature_id: str, feature_type: str, chainage: str) -> bool:
    """创建特征节点"""
    db = get_graph_db()
    
    # 创建特征
    db.merge_node("Feature", "id", feature_id, {
        "id": feature_id,
        "type": feature_type,
        "chainage": chainage
    })
    
    # 建立关系
    return db.create_relationship(
        "Drawing", "name", drawing_name,
        "HAS_FEATURE",
        "Feature", "id", feature_id
    )


def link_feature_to_coordinate(feature_id: str, x: float, y: float, z: float, chainage: str) -> bool:
    """关联特征与坐标"""
    db = get_graph_db()
    
    coord_id = f"coord_{chainage}"
    
    # 创建坐标节点
    db.merge_node("Coordinate", "id", coord_id, {
        "id": coord_id,
        "x": x,
        "y": y,
        "z": z,
        "chainage": chainage
    })
    
    # 建立关系
    return db.create_relationship(
        "Feature", "id", feature_id,
        "LOCATED_AT",
        "Coordinate", "id", coord_id
    )


def query_elevation(chainage: str) -> float:
    """查询指定桩号的高程"""
    db = get_graph_db()
    
    query = """
    MATCH (f:Feature {chainage: $chainage})-[:LOCATED_AT]->(c:Coordinate)
    RETURN c.z AS elevation
    """
    
    results = db.execute_query(query, {"chainage": chainage})
    return results[0].get("elevation") if results else None


if __name__ == "__main__":
    init_schema()
