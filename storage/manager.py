# -*- coding: utf-8 -*-
"""
存储管理器
提供简洁的API供其他模块调用
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# 导入模型
from storage.db.models import (
    engine, Session, Base,
    Project, Route, RouteParameter, CalculationResult,
    init_db, create_sample_data
)


class StorageManager:
    """
    存储管理器
    
    负责项目和参数的CRUD操作
    """
    
    def __init__(self):
        self.session = None
        # 自动初始化数据库
        init_db()
    
    def _init(self):
        """初始化"""
        init_db()
    
    def _get_session(self) -> Session:
        """获取会话"""
        if self.session is None:
            self.session = Session()
        return self.session
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()
            self.session = None
    
    # ========== 项目操作 ==========
    
    def create_project(self, name: str, description: str = "") -> Project:
        """创建项目"""
        session = self._get_session()
        
        project = Project(name=name, description=description)
        session.add(project)
        session.commit()
        session.refresh(project)
        
        return project
    
    def get_project(self, project_id: int = None, name: str = None) -> Optional[Project]:
        """获取项目"""
        session = self._get_session()
        
        if project_id:
            return session.query(Project).filter(Project.id == project_id).first()
        elif name:
            return session.query(Project).filter(Project.name == name).first()
        return None
    
    def list_projects(self) -> List[Project]:
        """列出所有项目"""
        session = self._get_session()
        return session.query(Project).order_by(Project.updated_at.desc()).all()
    
    def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        """更新项目"""
        session = self._get_session()
        
        project = session.query(Project).filter(Project.id == project_id).first()
        if project:
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            project.updated_at = datetime.now()
            session.commit()
            session.refresh(project)
        
        return project
    
    def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        session = self._get_session()
        
        project = session.query(Project).filter(Project.id == project_id).first()
        if project:
            session.delete(project)
            session.commit()
            return True
        return False
    
    # ========== 路线操作 ==========
    
    def create_route(self, project_id: int, name: str, **kwargs) -> Route:
        """创建路线"""
        session = self._get_session()
        
        route = Route(project_id=project_id, name=name, **kwargs)
        session.add(route)
        session.commit()
        session.refresh(route)
        
        return route
    
    def get_route(self, route_id: int = None, name: str = None) -> Optional[Route]:
        """获取路线"""
        session = self._get_session()
        
        if route_id:
            return session.query(Route).filter(Route.id == route_id).first()
        elif name:
            return session.query(Route).filter(Route.name == name).first()
        return None
    
    def list_routes(self, project_id: int = None) -> List[Route]:
        """列出路线"""
        session = self._get_session()
        
        query = session.query(Route)
        if project_id:
            query = query.filter(Route.project_id == project_id)
        
        return query.order_by(Route.start_station).all()
    
    def delete_route(self, route_id: int) -> bool:
        """删除路线"""
        session = self._get_session()
        
        route = session.query(Route).filter(Route.id == route_id).first()
        if route:
            session.delete(route)
            session.commit()
            return True
        return False
    
    # ========== 参数操作 ==========
    
    def save_parameters(self, route_id: int, params: Dict, source: str = "manual", 
                      confidence: float = 1.0, description: str = "") -> RouteParameter:
        """保存参数"""
        session = self._get_session()
        
        # 获取版本号
        last = session.query(RouteParameter).filter(
            RouteParameter.route_id == route_id
        ).order_by(RouteParameter.version.desc()).first()
        
        version = (last.version + 1) if last else 1
        
        param = RouteParameter(
            route_id=route_id,
            version=version,
            horizontal_json=json.dumps(params.get("horizontal_alignment", [])),
            vertical_json=json.dumps(params.get("vertical_alignment", [])),
            cross_section_json=json.dumps(params.get("cross_section_template", {})),
            structures_json=json.dumps(params.get("structures", [])),
            source=source,
            confidence=confidence,
            description=description
        )
        
        session.add(param)
        session.commit()
        session.refresh(param)
        
        return param
    
    def get_parameters(self, route_id: int, version: int = None) -> Optional[Dict]:
        """获取参数"""
        session = self._get_session()
        
        query = session.query(RouteParameter).filter(RouteParameter.route_id == route_id)
        
        if version:
            query = query.filter(RouteParameter.version == version)
        else:
            query = query.order_by(RouteParameter.version.desc())
        
        param = query.first()
        
        if param:
            return {
                "route_id": param.route_id,
                "version": param.version,
                "horizontal_alignment": json.loads(param.horizontal_json or "[]"),
                "vertical_alignment": json.loads(param.vertical_json or "[]"),
                "cross_section_template": json.loads(param.cross_section_json or "{}"),
                "structures": json.loads(param.structures_json or "[]"),
                "source": param.source,
                "confidence": param.confidence,
                "created_at": param.created_at.isoformat() if param.created_at else None,
                "description": param.description
            }
        
        return None
    
    def get_parameter_versions(self, route_id: int) -> List[Dict]:
        """获取参数版本历史"""
        session = self._get_session()
        
        params = session.query(RouteParameter).filter(
            RouteParameter.route_id == route_id
        ).order_by(RouteParameter.version.desc()).all()
        
        return [
            {
                "version": p.version,
                "source": p.source,
                "confidence": p.confidence,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "description": p.description
            }
            for p in params
        ]
    
    # ========== 计算结果操作 ==========
    
    def save_calculation(self, route_id: int, station: float, x: float, y: float, 
                        z: float, azimuth: float, lod: str = "LOD1") -> CalculationResult:
        """保存计算结果"""
        session = self._get_session()
        
        # 检查是否已存在
        existing = session.query(CalculationResult).filter(
            CalculationResult.route_id == route_id,
            CalculationResult.station == station,
            CalculationResult.lod == lod
        ).first()
        
        if existing:
            existing.x = x
            existing.y = y
            existing.z = z
            existing.azimuth = azimuth
            existing.calculated_at = datetime.now()
            session.commit()
            return existing
        
        result = CalculationResult(
            route_id=route_id,
            station=station,
            x=x, y=y, z=z, azimuth=azimuth,
            lod=lod
        )
        
        session.add(result)
        session.commit()
        session.refresh(result)
        
        return result
    
    def get_calculation(self, route_id: int, station: float, lod: str = "LOD1") -> Optional[Dict]:
        """获取计算结果"""
        session = self._get_session()
        
        result = session.query(CalculationResult).filter(
            CalculationResult.route_id == route_id,
            CalculationResult.station == station,
            CalculationResult.lod == lod
        ).first()
        
        if result:
            return {
                "station": result.station,
                "x": result.x,
                "y": result.y,
                "z": result.z,
                "azimuth": result.azimuth,
                "lod": result.lod,
                "calculated_at": result.calculated_at.isoformat() if result.calculated_at else None
            }
        
        return None
    
    def get_calculations(self, route_id: int, start: float = None, 
                        end: float = None) -> List[Dict]:
        """获取计算结果列表"""
        session = self._get_session()
        
        query = session.query(CalculationResult).filter(
            CalculationResult.route_id == route_id
        )
        
        if start is not None:
            query = query.filter(CalculationResult.station >= start)
        if end is not None:
            query = query.filter(CalculationResult.station <= end)
        
        results = query.order_by(CalculationResult.station).all()
        
        return [
            {
                "station": r.station,
                "x": r.x, "y": r.y, "z": r.z,
                "azimuth": r.azimuth,
                "lod": r.lod
            }
            for r in results
        ]
    
    def clear_calculations(self, route_id: int) -> int:
        """清除计算结果"""
        session = self._get_session()
        
        count = session.query(CalculationResult).filter(
            CalculationResult.route_id == route_id
        ).delete()
        
        session.commit()
        return count


# 全局实例
_storage = None


def get_storage() -> StorageManager:
    """获取存储管理器实例"""
    global _storage
    if _storage is None:
        _storage = StorageManager()
    return _storage


# 初始化示例数据
def init_sample():
    """初始化示例数据"""
    create_sample_data()


if __name__ == "__main__":
    init_sample()
    
    # 测试
    sm = get_storage()
    
    # 列出项目
    projects = sm.list_projects()
    print(f"项目数: {len(projects)}")
    
    for p in projects:
        print(f"  - {p.name}")
    
    # 列出路线
    if projects:
        routes = sm.list_routes(projects[0].id)
        print(f"路线数: {len(routes)}")
        
        for r in routes:
            print(f"  - {r.name}")
            
            # 获取参数
            params = sm.get_parameters(r.id)
            if params:
                print(f"    参数版本: {params['version']}")
