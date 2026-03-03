# -*- coding: utf-8 -*-
"""
数据库模型
使用SQLAlchemy
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 数据库路径
DB_PATH = os.environ.get("NEURALSITE_DB", "neuralsite.db")

# 创建引擎
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# 创建基类
Base = declarative_base()

# 创建会话
Session = sessionmaker(bind=engine)


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    routes = relationship("Route", back_populates="project")
    
    def __repr__(self):
        return f"<Project {self.name}>"


class Route(Base):
    """路线模型"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)  # 路线名称，如"K0+000 - K10+000"
    route_type = Column(String(50), default="highway")  # highway/bridge/tunnel
    
    design_speed = Column(Integer, default=80)  # 设计速度 km/h
    start_station = Column(Float, default=0)  # 起点桩号(m)
    end_station = Column(Float, default=0)  # 终点桩号(m)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    project = relationship("Project", back_populates="routes")
    parameters = relationship("RouteParameter", back_populates="route")
    calculations = relationship("CalculationResult", back_populates="route")
    
    def __repr__(self):
        return f"<Route {self.name}>"


class RouteParameter(Base):
    """路线参数模型 - 存储JSON参数"""
    __tablename__ = "route_parameters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    version = Column(Integer, default=1)  # 版本号
    
    # JSON存储
    horizontal_json = Column(Text)  # 平曲线参数
    vertical_json = Column(Text)    # 纵曲线参数
    cross_section_json = Column(Text)  # 横断面参数
    structures_json = Column(Text)  # 结构物参数
    
    # 元数据
    source = Column(String(100))  # 来源: manual/parser/file
    confidence = Column(Float, default=1.0)  # 置信度
    
    created_at = Column(DateTime, default=datetime.now)
    description = Column(String(500))  # 描述
    
    # 关联
    route = relationship("Route", back_populates="parameters")
    
    def __repr__(self):
        return f"<RouteParameter route={self.route_id} v={self.version}>"


class CalculationResult(Base):
    """计算结果缓存"""
    __tablename__ = "calculation_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    
    station = Column(Float, nullable=False, index=True)  # 桩号
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    azimuth = Column(Float)
    
    lod = Column(String(10), default="LOD1")  # LOD级别
    calculated_at = Column(DateTime, default=datetime.now)
    
    # 关联
    route = relationship("Route", back_populates="calculations")
    
    def __repr__(self):
        return f"<CalculationResult station={self.station}>"


# 初始化数据库
def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(engine)


# 创建示例数据
def create_sample_data():
    """创建示例数据"""
    session = Session()
    
    try:
        # 检查是否已有数据
        if session.query(Project).first():
            return
        
        # 创建项目
        project = Project(
            name="示例高速公路项目",
            description="这是一条示例高速公路"
        )
        session.add(project)
        session.flush()
        
        # 创建路线
        route = Route(
            project_id=project.id,
            name="主线K0-K2",
            design_speed=80,
            start_station=0,
            end_station=2000
        )
        session.add(route)
        session.flush()
        
        # 创建参数
        import json
        param = RouteParameter(
            route_id=route.id,
            version=1,
            horizontal_json=json.dumps([
                {"element_type": "直线", "start_station": "K0+000", "end_station": "K0+500",
                 "azimuth": 45, "x0": 500000, "y0": 3000000},
                {"element_type": "缓和曲线", "start_station": "K0+500", "end_station": "K0+600",
                 "azimuth": 45, "x0": 500353.553, "y0": 3000353.553, "A": 300, "R": 800, "direction": "右"},
                {"element_type": "圆曲线", "start_station": "K0+600", "end_station": "K1+200",
                 "azimuth": 45, "x0": 500424.264, "y0": 3000424.264, "R": 800,
                 "cx": 500424.264, "cy": 3000224.264, "direction": "右"}
            ]),
            vertical_json=json.dumps([
                {"station": "K0+000", "elevation": 100, "grade_out": 20},
                {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "length": 200},
                {"station": "K1+200", "elevation": 99.5, "grade_in": -15}
            ]),
            cross_section_json=json.dumps({"width": 26, "lanes": 4, "crown_slope": 2.0}),
            source="parser",
            confidence=0.95
        )
        session.add(param)
        
        session.commit()
        print("示例数据创建完成")
        
    except Exception as e:
        session.rollback()
        print(f"错误: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    create_sample_data()
    print(f"数据库初始化完成: {DB_PATH}")
