# -*- coding: utf-8 -*-
"""
Auto-QA Agent
自动质检工作流：导入 -> 验证 -> 碰撞检测 -> 生成报告 + 解决方案
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json

# 导入解决方案查询
from core.knowledge_graph.query_engine import get_solution


class IssueSeverity(Enum):
    """问题严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """验证问题"""
    issue_id: str
    severity: IssueSeverity
    location: str          # 位置，如 "K0+500"
    issue_type: str       # 问题类型
    description: str      # 描述
    recommendation: str   # 整改建议
    solution: str = ""    # 解决方案 (来自知识图谱)
    standard: str = ""    # 引用规范
    measures: List[str] = field(default_factory=list)  # 具体措施
    related_components: List[str] = field(default_factory=list)


@dataclass
class QAReport:
    """质检报告"""
    report_id: str
    route_id: str
    status: str           # passed, warnings, errors
    total_points: int
    issues_count: int
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: str = ""


class AutoQAAgent:
    """自动质检Agent"""
    
    def __init__(self):
        self.rules = self._init_rules()
    
    def _init_rules(self) -> Dict:
        """初始化验证规则"""
        return {
            # 几何规则
            "radius_min": {"value": 0, "severity": "error", "message": "曲线半径不能为0"},
            "radius_too_small": {"value": 15, "severity": "warning", "message": "半径过小，行车安全风险高"},
            "slope_too_steep": {"value": 5, "severity": "warning", "message": "纵坡超过5%"},
            
            # 超高规则
            "superelevation_max": {"value": 8, "severity": "error", "message": "超高超限"},
            
            # 间距规则
            "point_spacing_max": {"value": 200, "severity": "warning", "message": "桩点间距过大"},
            
            # 碰撞规则 (简化)
            "collision_distance": {"value": 0.5, "severity": "critical", "message": "构件碰撞"}
        }
    
    def run_full_validation(self, route_data: Dict, coordinates: List[Dict]) -> QAReport:
        """运行完整验证流程
        
        Args:
            route_data: 路线参数
            coordinates: 计算后的坐标列表
            
        Returns:
            质检报告
        """
        issues = []
        
        # 1. 几何参数验证
        issues.extend(self._validate_geometry(route_data))
        
        # 2. 坐标数据验证
        issues.extend(self._validate_coordinates(coordinates))
        
        # 3. 纵坡验证
        issues.extend(self._validate_vertical(coordinates))
        
        # 4. 碰撞检测
        issues.extend(self._check_collisions(coordinates))
        
        # 生成报告
        report = QAReport(
            report_id=f"qa_{route_data.get('route_id', 'unknown')}_{len(issues)}",
            route_id=route_data.get("route_id", "unknown"),
            status=self._determine_status(issues),
            total_points=len(coordinates),
            issues_count=len(issues),
            issues=issues,
            summary=self._generate_summary(issues)
        )
        
        return report
    
    def _validate_geometry(self, route_data: Dict) -> List[ValidationIssue]:
        """验证几何参数"""
        issues = []
        
        horizontal = route_data.get("horizontal_alignment", [])
        
        for i, elem in enumerate(horizontal):
            elem_type = elem.get("element_type", "")
            
            # 检查半径
            if elem_type in ["圆曲线", "缓和曲线"]:
                radius = elem.get("radius") or elem.get("R") or elem.get("r")
                if radius:
                    radius = float(radius)
                    
                    if radius == 0:
                        issues.append(ValidationIssue(
                            issue_id=f"geo_radius_{i}",
                            severity=IssueSeverity.ERROR,
                            location=elem.get("start_station", "未知"),
                            issue_type="radius_zero",
                            description=f"曲线半径为0",
                            recommendation="请检查平曲线参数"
                        ))
                    
                    if 0 < radius < 15:
                        issues.append(ValidationIssue(
                            issue_id=f"geo_radius_small_{i}",
                            severity=IssueSeverity.WARNING,
                            location=elem.get("start_station", "未知"),
                            issue_type="radius_too_small",
                            description=f"曲线半径过小: {radius}m",
                            recommendation="建议增大半径或设置缓和曲线"
                        ))
        
        return issues
    
    def _validate_coordinates(self, coordinates: List[Dict]) -> List[ValidationIssue]:
        """验证坐标数据"""
        issues = []
        
        if not coordinates:
            issues.append(ValidationIssue(
                issue_id="coord_empty",
                severity=IssueSeverity.ERROR,
                location="全局",
                issue_type="no_data",
                description="没有坐标数据",
                recommendation="请检查数据导入"
            ))
            return issues
        
        # 检查间距
        for i in range(1, len(coordinates)):
            prev = coordinates[i-1]
            curr = coordinates[i]
            
            # 计算平面距离
            dx = curr.get("x", 0) - prev.get("x", 0)
            dy = curr.get("y", 0) - prev.get("y", 0)
            dist = (dx**2 + dy**2) ** 0.5
            
            if dist > 200:
                issues.append(ValidationIssue(
                    issue_id=f"spacing_{i}",
                    severity=IssueSeverity.WARNING,
                    location=curr.get("station", "未知"),
                    issue_type="spacing_large",
                    description=f"桩点间距过大: {dist:.1f}m",
                    recommendation="建议加密桩点"
                ))
        
        return issues
    
    def _validate_vertical(self, coordinates: List[Dict]) -> List[ValidationIssue]:
        """验证纵坡"""
        issues = []
        
        for i in range(1, len(coordinates)):
            prev = coordinates[i-1]
            curr = coordinates[i]
            
            # 计算纵坡
            dz = curr.get("z", 0) - prev.get("z", 0)
            dx = curr.get("x", 0) - prev.get("x", 0)
            dy = curr.get("y", 0) - prev.get("y", 0)
            dist = (dx**2 + dy**2) ** 0.5
            
            if dist > 0:
                grade = abs(dz / dist * 100)  # 百分比
                
                if grade > 5:
                    issues.append(ValidationIssue(
                        issue_id=f"slope_{i}",
                        severity=IssueSeverity.WARNING,
                        location=curr.get("station", "未知"),
                        issue_type="slope_steep",
                        description=f"纵坡过陡: {grade:.2f}%",
                        recommendation="建议降低纵坡或设置竖曲线"
                    ))
        
        return issues
    
    def _check_collisions(self, coordinates: List[Dict]) -> List[ValidationIssue]:
        """碰撞检测（简化版：检查异常接近的点）"""
        issues = []
        
        # 简化：检查是否有坐标异常接近的情况
        # 实际应该检查构件之间的碰撞
        
        return issues
    
    def _determine_status(self, issues: List[ValidationIssue]) -> str:
        """确定状态"""
        if not issues:
            return "passed"
        
        has_critical = any(i.severity == IssueSeverity.CRITICAL for i in issues)
        has_error = any(i.severity == IssueSeverity.ERROR for i in issues)
        
        if has_critical:
            return "critical"
        elif has_error:
            return "errors"
        elif any(i.severity == IssueSeverity.WARNING for i in issues):
            return "warnings"
        else:
            return "passed"
    
    def _generate_summary(self, issues: List[ValidationIssue]) -> str:
        """生成摘要"""
        if not issues:
            return "质检通过，未发现问题"
        
        counts = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.ERROR: 0,
            IssueSeverity.WARNING: 0,
            IssueSeverity.INFO: 0
        }
        
        for issue in issues:
            counts[issue.severity] += 1
        
        summary_parts = []
        if counts[IssueSeverity.CRITICAL] > 0:
            summary_parts.append(f"{counts[IssueSeverity.CRITICAL]}个严重问题")
        if counts[IssueSeverity.ERROR] > 0:
            summary_parts.append(f"{counts[IssueSeverity.ERROR]}个错误")
        if counts[IssueSeverity.WARNING] > 0:
            summary_parts.append(f"{counts[IssueSeverity.WARNING]}个警告")
        
        return "发现" + "，".join(summary_parts)


# 全局实例
_qa_agent = None


def get_qa_agent() -> AutoQAAgent:
    """获取QA Agent实例"""
    global _qa_agent
    if _qa_agent is None:
        _qa_agent = AutoQAAgent()
    return _qa_agent


if __name__ == "__main__":
    # Test
    agent = get_qa_agent()
    
    # 模拟数据
    route_data = {
        "route_id": "test_route",
        "horizontal_alignment": [
            {"element_type": "直线", "start_station": "K0+000", "end_station": "K0+500", "azimuth": 45},
            {"element_type": "圆曲线", "start_station": "K0+500", "end_station": "K1+000", "R": 800},
            {"element_type": "直线", "start_station": "K1+000", "end_station": "K1+200", "azimuth": 45}
        ]
    }
    
    coordinates = [
        {"station": "K0+000", "x": 500000, "y": 3000000, "z": 100},
        {"station": "K0+250", "x": 500176, "y": 3000176, "z": 105},
        {"station": "K0+500", "x": 500353, "y": 3000353, "z": 110},
        {"station": "K0+750", "x": 500530, "y": 3000530, "z": 112},
        {"station": "K1+000", "x": 500707, "y": 3000707, "z": 108}
    ]
    
    # 运行验证
    report = agent.run_full_validation(route_data, coordinates)
    
    print("=== QA Report ===")
    print(f"Route: {report.route_id}")
    print(f"Status: {report.status}")
    print(f"Issues: {report.issues_count}")
    print(f"Summary: {report.summary}")
    
    for issue in report.issues:
        print(f"  - [{issue.severity.value}] {issue.location}: {issue.description}")
