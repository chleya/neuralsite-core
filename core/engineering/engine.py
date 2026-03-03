# -*- coding: utf-8 -*-
"""
工程智能引擎
包含：施工工艺推荐、BIM模型生成、碰撞检测
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class ConstructionMethod(Enum):
    """施工工艺"""
    CNC_CUTTING = "数控切割"           # 数控切割
    FIELD_WELDING = "现场焊接"         # 现场焊接
    PREFABRICATION = "预制装配"         # 预制装配
    CAST_IN_PLACE = "现浇混凝土"        # 现浇混凝土
    LIFTING = "整体吊装"               # 整体吊装
    PRECISION_MACHINING = "精密机加工"  # 精密机加工


class MaterialType(Enum):
    """材料类型"""
    Q345B = "Q345B"          # 钢结构
    C30 = "C30"              # 混凝土
    C40 = "C40"              # 高强度混凝土
    STEEL_PLATE = "钢板"     # 钢板


@dataclass
class ConstructionRecommendation:
    """施工工艺推荐结果"""
    method: str
    confidence: float  # 0-1
    reasons: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)


@dataclass
class QualityControl:
    """质量控制点"""
    point_id: str
    name: str
    standard_value: float
    tolerance: float  # 公差
    test_method: str
    location: Dict[str, float] = field(default_factory=dict)  # x, y, z


class EngineeringIntelligence:
    """工程智能引擎"""
    
    def __init__(self):
        # 工艺规则库
        self.rules = self._init_rules()
    
    def _init_rules(self) -> Dict:
        """初始化工艺规则库"""
        return {
            # 异形钢构件规则
            "abnormal_steel": {
                "conditions": {
                    "material": ["Q345B", "Q235"],
                    "complexity": "high"
                },
                "recommended_methods": [
                    {
                        "method": ConstructionMethod.CNC_CUTTING.value,
                        "confidence": 0.95,
                        "reasons": ["精度要求高", "形状复杂"],
                        "constraints": ["需要数控设备"],
                        "resources": ["数控切割机", "焊接设备"]
                    },
                    {
                        "method": ConstructionMethod.FIELD_WELDING.value,
                        "confidence": 0.7,
                        "reasons": ["现场拼接"],
                        "constraints": ["现场条件", "焊接质量控制"],
                        "resources": ["焊工", "焊接设备"]
                    }
                ]
            },
            
            # 预制构件规则
            "prefab": {
                "conditions": {
                    "type": ["prefab"],
                    "size": "<=50"  # 米
                },
                "recommended_methods": [
                    {
                        "method": ConstructionMethod.PREFABRICATION.value,
                        "confidence": 0.9,
                        "reasons": ["工厂预制", "质量可控"],
                        "constraints": ["运输限制"],
                        "resources": ["预制厂", "运输设备"]
                    },
                    {
                        "method": ConstructionMethod.LIFTING.value,
                        "confidence": 0.85,
                        "reasons": ["装配施工"],
                        "constraints": ["起重能力"],
                        "resources": ["吊车", "安装团队"]
                    }
                ]
            },
            
            # 混凝土构件规则
            "concrete": {
                "conditions": {
                    "material": ["C30", "C40", "C50"]
                },
                "recommended_methods": [
                    {
                        "method": ConstructionMethod.CAST_IN_PLACE.value,
                        "confidence": 0.9,
                        "reasons": ["整体性好"],
                        "constraints": ["养护时间"],
                        "resources": ["混凝土搅拌站", "振捣设备"]
                    }
                ]
            }
        }
    
    def recommend_construction_method(
        self, 
        component_type: str,
        material: str = "Q345B",
        complexity: str = "high",
        size: Dict[str, float] = None,
        site_conditions: Dict[str, Any] = None
    ) -> List[ConstructionRecommendation]:
        """施工工艺推荐"""
        
        recommendations = []
        
        # 根据构件类型匹配规则
        if "abnormal" in component_type.lower() or "column" in component_type.lower():
            rule_set = self.rules.get("abnormal_steel", {})
        elif "prefab" in component_type.lower():
            rule_set = self.rules.get("prefab", {})
        else:
            rule_set = self.rules.get("concrete", {})
        
        for method_info in rule_set.get("recommended_methods", []):
            rec = ConstructionRecommendation(
                method=method_info["method"],
                confidence=method_info["confidence"],
                reasons=method_info.get("reasons", []),
                constraints=method_info.get("constraints", []),
                resources=method_info.get("resources", [])
            )
            recommendations.append(rec)
        
        # 根据现场条件过滤
        if site_conditions:
            for rec in recommendations:
                # 检查设备可用性
                if "equipment" in site_conditions:
                    available = site_conditions["equipment"]
                    rec.constraints.append(f"现场可用设备: {', '.join(available)}")
        
        return recommendations
    
    def detect_collision(
        self,
        component1: Dict,
        component2: Dict,
        lod_level: int = 1
    ) -> Dict:
        """碰撞检测
        
        LOD0: 米级精度，快速检测
        LOD1: 分米级精度，常规检测
        LOD2: 厘米级精度，精确定位
        """
        
        # 获取两个构件的位置
        pos1 = component1.get("parameters", {})
        pos2 = component2.get("parameters", {})
        
        # 简化计算：检查边界框是否相交
        tolerance = {
            0: 1.0,   # 米
            1: 0.1,   # 分米
            2: 0.01   # 厘米
        }
        
        tol = tolerance.get(lod_level, 0.1)
        
        # 计算距离（简化版）
        dx = abs(pos1.get("x", 0) - pos2.get("x", 0))
        dy = abs(pos1.get("y", 0) - pos2.get("y", 0))
        dz = abs(pos1.get("z", 0) - pos2.get("z", 0))
        
        # 简化：假设两个构件的大小
        size1 = pos1.get("size", 1.0)
        size2 = pos2.get("size", 1.0)
        
        min_dist = (size1 + size2) / 2 + tol
        
        collision = dx < min_dist and dy < min_dist and dz < min_dist
        
        return {
            "collision_detected": collision,
            "distance": {
                "x": dx,
                "y": dy,
                "z": dz,
                "total": (dx**2 + dy**2 + dz**2) ** 0.5
            },
            "lod_level": lod_level,
            "tolerance": tol,
            "status": "COLLISION" if collision else "CLEAR"
        }
    
    def generate_quality_control_plan(
        self,
        component: Dict
    ) -> List[QualityControl]:
        """生成质量控制计划"""
        
        qc_points = []
        component_type = component.get("type", "")
        
        # 根据构件类型生成质量控制点
        if "abnormal" in component_type.lower() or "column" in component_type.lower():
            # 异形柱质量控制点
            qc_points.append(QualityControl(
                point_id="QC-001",
                name="顶部标高",
                standard_value=component.get("parameters", {}).get("totalHeight", 0),
                tolerance=0.01,  # 厘米级
                test_method="水准仪",
                location={"x": 0, "y": 0, "z": component.get("parameters", {}).get("totalHeight", 0)}
            ))
            
            qc_points.append(QualityControl(
                point_id="QC-002",
                name="垂直度",
                standard_value=0,
                tolerance=0.005,  # 0.5%
                test_method="经纬仪"
            ))
            
            qc_points.append(QualityControl(
                point_id="QC-003",
                name="焊接质量",
                standard_value=0,
                tolerance=0,
                test_method="超声波探伤"
            ))
        
        return qc_points
    
    def export_to_bim_format(self, component: Dict, format: str = "revit") -> Dict:
        """导出为BIM格式
        
        支持: revit, tekla, ifc
        """
        
        if format == "revit":
            return self._to_revit_family(component)
        elif format == "tekla":
            return self._to_tekla(component)
        elif format == "ifc":
            return self._to_ifc(component)
        else:
            return {"error": f"Unsupported format: {format}"}
    
    def _to_revit_family(self, component: Dict) -> Dict:
        """转换为Revit参数化族"""
        
        params = component.get("parameters", {})
        
        return {
            "family_name": component.get("componentId", "Unknown"),
            "family_category": "Structural Columns",
            "parameters": [
                {
                    "name": "Width",
                    "type": "Number",
                    "value": params.get("width", 0),
                    "unit": "meters"
                },
                {
                    "name": "Height", 
                    "type": "Number",
                    "value": params.get("height", 0),
                    "unit": "meters"
                },
                {
                    "name": "TotalHeight",
                    "type": "Number",
                    "value": params.get("totalHeight", 0),
                    "unit": "meters"
                },
                {
                    "name": "Slope",
                    "type": "Number",
                    "value": params.get("slope", 0),
                    "unit": "percent"
                },
                {
                    "name": "CornerRadius",
                    "type": "Number",
                    "value": params.get("cornerRadius", 0),
                    "unit": "meters"
                },
                {
                    "name": "Material",
                    "type": "Text",
                    "value": params.get("material", "Q345B")
                }
            ],
            "formula": "Height = TotalHeight - Slope * Width",
            "notes": "参数化异形柱族"
        }
    
    def _to_tekla(self, component: Dict) -> Dict:
        """转换为Tekla模型"""
        
        params = component.get("parameters", {})
        
        return {
            "model_object": {
                "type": "COLUMN",
                "profile": "PLATE",
                "material": params.get("material", "Q345B")
            },
            "dimensions": {
                "width": params.get("width", 0) * 1000,  # 转换为mm
                "height": params.get("height", 0) * 1000,
                "thickness": 10  # 默认厚度
            },
            "welding": {
                "method": "CNC_CUTTING",
                "tolerance": "ISO 9013"
            }
        }
    
    def _to_ifc(self, component: Dict) -> Dict:
        """转换为IFC格式"""
        
        return {
            "ifcEntity": "IfcColumn",
            "name": component.get("componentId", "Unknown"),
            "description": component.get("description", ""),
            "parameters": component.get("parameters", {}),
            "lod": component.get("loDLevels", [])[-1].get("level", 0) if component.get("loDLevels") else 0
        }


# 全局实例
_engineering_intel = None


def get_engineering_intel() -> EngineeringIntelligence:
    """获取工程智能引擎"""
    global _engineering_intel
    if _engineering_intel is None:
        _engineering_intel = EngineeringIntelligence()
    return _engineering_intel


if __name__ == "__main__":
    # 测试
    engine = get_engineering_intel()
    
    # 测试施工推荐
    component = {
        "type": "AbnormalColumn",
        "componentId": "test-001",
        "parameters": {
            "width": 0.8,
            "height": 1.2,
            "totalHeight": 3.5,
            "material": "Q345B"
        }
    }
    
    print("=== 施工工艺推荐 ===")
    recs = engine.recommend_construction_method(
        component_type="AbnormalColumn",
        material="Q345B",
        complexity="high"
    )
    
    for rec in recs:
        print(f"方法: {rec.method}")
        print(f"置信度: {rec.confidence:.0%}")
        print(f"原因: {', '.join(rec.reasons)}")
        print(f"资源: {', '.join(rec.resources)}")
        print()
    
    # 测试BIM导出
    print("=== Revit参数化族 ===")
    revit = engine.export_to_bim_format(component, "revit")
    print(json.dumps(revit, indent=2, ensure_ascii=False))
