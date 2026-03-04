# -*- coding: utf-8 -*-
"""
PostGIS Spatial Database Module
空间数据库模块 - 存储和查询空间数据
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import json


@dataclass
class SpatialPoint:
    """空间点"""
    id: Optional[int]
    project_id: int
    chainage: str        # 桩号
    point_type: str      # 点类型
    x: float             # X坐标
    y: float             # Y坐标
    z: float = 0.0       # 高程
    azimuth: float = 0   # 方位角
    properties: Dict = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class SpatialDatabase:
    """空间数据库接口
    
    支持PostGIS或SQLite fallback
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        self.db_type = self._detect_db_type(connection_string)
        self._client = None
    
    def _detect_db_type(self, connection_string: str) -> str:
        """检测数据库类型"""
        if not connection_string:
            return "memory"
        
        if "postgresql" in connection_string.lower():
            return "postgresql"
        elif "sqlite" in connection_string.lower():
            return "sqlite"
        else:
            return "memory"
    
    def connect(self):
        """连接数据库"""
        if self.db_type == "postgresql":
            self._connect_postgres()
        elif self.db_type == "sqlite":
            self._connect_sqlite()
        else:
            # 内存模式
            self._points = []
    
    def _connect_postgres(self):
        """连接PostgreSQL"""
        try:
            import psycopg2
            self._client = psycopg2.connect(self.connection_string)
            print(f"Connected to PostgreSQL: {self.connection_string[:30]}...")
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}, using memory mode")
            self.db_type = "memory"
            self._points = []
    
    def _connect_sqlite(self):
        """连接SQLite"""
        import sqlite3
        self._client = sqlite3.connect(self.connection_string or ":memory:")
    
    def add_point(self, point: SpatialPoint) -> int:
        """添加空间点"""
        if self.db_type == "memory":
            point.id = len(self._points) + 1
            self._points.append(point)
            return point.id
        
        if self.db_type == "postgresql":
            return self._add_point_postgres(point)
        
        if self.db_type == "sqlite":
            return self._add_point_sqlite(point)
    
    def _add_point_postgres(self, point: SpatialPoint) -> int:
        """PostgreSQL添加点"""
        query = """
        INSERT INTO spatial_points 
            (project_id, chainage, point_type, geom, elevation, azimuth, properties)
        VALUES 
            (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4490), %s, %s, %s)
        RETURNING id
        """
        cursor = self._client.cursor()
        cursor.execute(query, (
            point.project_id,
            point.chainage,
            point.point_type,
            point.x,
            point.y,
            point.z,
            point.azimuth,
            json.dumps(point.properties)
        ))
        self._client.commit()
        return cursor.fetchone()[0]
    
    def _add_point_sqlite(self, point: SpatialPoint) -> int:
        """SQLite添加点"""
        query = """
        INSERT INTO spatial_points 
            (project_id, chainage, point_type, x, y, z, azimuth, properties)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._client.cursor()
        cursor.execute(query, (
            point.project_id,
            point.chainage,
            point.point_type,
            point.x,
            point.y,
            point.z,
            point.azimuth,
            json.dumps(point.properties)
        ))
        self._client.commit()
        return cursor.lastrowid
    
    def query_nearby(
        self, 
        x: float, 
        y: float, 
        radius_meters: float,
        project_id: int = None
    ) -> List[SpatialPoint]:
        """查询附近的空间点
        
        Args:
            x: 中心点X
            y: 中心点Y
            radius_meters: 查询半径(米)
            project_id: 项目ID过滤
            
        Returns:
            附近的空间点列表
        """
        if self.db_type == "memory":
            return self._query_nearby_memory(x, y, radius_meters, project_id)
        
        if self.db_type == "postgresql":
            return self._query_nearby_postgis(x, y, radius_meters, project_id)
        
        return []
    
    def _query_nearby_memory(
        self, 
        x: float, 
        y: float, 
        radius_meters: float,
        project_id: int = None
    ) -> List[SpatialPoint]:
        """内存模式: 简单距离查询"""
        results = []
        for p in self._points:
            if project_id and p.project_id != project_id:
                continue
            
            # 简单距离计算
            dx = p.x - x
            dy = p.y - y
            dist = (dx*dx + dy*dy) ** 0.5
            
            if dist <= radius_meters:
                results.append(p)
        
        return results
    
    def _query_nearby_postgis(
        self, 
        x: float, 
        y: float, 
        radius_meters: float,
        project_id: int = None
    ) -> List[SpatialPoint]:
        """PostGIS: 空间查询"""
        query = """
        SELECT id, project_id, chainage, point_type, 
               ST_X(geom) as x, ST_Y(geom) as y,
               elevation, azimuth, properties
        FROM spatial_points
        WHERE ST_DWithin(
            geom,
            ST_SetSRID(ST_MakePoint(%s, %s), 4490),
            %s
        )
        """
        params = [x, y, radius_meters]
        
        if project_id:
            query += " AND project_id = %s"
            params.append(project_id)
        
        cursor = self._client.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append(SpatialPoint(
                id=row[0],
                project_id=row[1],
                chainage=row[2],
                point_type=row[3],
                x=row[4],
                y=row[5],
                z=row[6] or 0,
                azimuth=row[7] or 0,
                properties=json.loads(row[8]) if row[8] else {}
            ))
        
        return results
    
    def query_by_chainage(
        self, 
        chainage_start: str, 
        chainage_end: str,
        project_id: int = None
    ) -> List[SpatialPoint]:
        """按桩号范围查询"""
        if self.db_type == "memory":
            return self._query_by_chainage_memory(chainage_start, chainage_end, project_id)
        
        # 简化: 返回空列表
        return []
    
    def _query_by_chainage_memory(
        self, 
        chainage_start: str, 
        chainage_end: str,
        project_id: int = None
    ) -> List[SpatialPoint]:
        """内存模式: 桩号查询"""
        # 简单实现
        def parse_chainage(c: str) -> float:
            if not c:
                return 0
            c = c.replace("K", "").replace("+", ".")
            try:
                return float(c)
            except:
                return 0
        
        start = parse_chainage(chainage_start)
        end = parse_chainage(chainage_end)
        
        results = []
        for p in self._points:
            if project_id and p.project_id != project_id:
                continue
            
            cp = parse_chainage(p.chainage)
            if start <= cp <= end:
                results.append(p)
        
        return results
    
    def close(self):
        """关闭连接"""
        if self._client:
            if self.db_type == "postgresql":
                self._client.close()
            elif self.db_type == "sqlite":
                self._client.close()


# 全局实例
_spatial_db = None


def get_spatial_db(connection_string: str = None) -> SpatialDatabase:
    """获取空间数据库实例"""
    global _spatial_db
    if _spatial_db is None:
        _spatial_db = SpatialDatabase(connection_string)
        _spatial_db.connect()
    return _spatial_db


# 测试
if __name__ == "__main__":
    # 内存模式测试
    db = get_spatial_db()
    
    # 添加测试点
    points = [
        SpatialPoint(None, 1, "K0+000", "centerline", 500000, 3000000, 100, 45),
        SpatialPoint(None, 1, "K0+100", "centerline", 500070, 3000070, 102, 45),
        SpatialPoint(None, 1, "K0+200", "centerline", 500141, 3000141, 104, 45),
    ]
    
    for p in points:
        db.add_point(p)
    
    # 查询附近点
    nearby = db.query_nearby(500070, 3000070, 100, project_id=1)
    print(f"Found {len(nearby)} nearby points")
    
    for p in nearby:
        print(f"  {p.chainage}: ({p.x}, {p.y})")
