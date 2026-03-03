# -*- coding: utf-8 -*-
"""
工作流引擎
自动执行: 导入 -> 计算 -> 质检 -> 报告
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json


@dataclass
class WorkflowResult:
    """工作流结果"""
    success: bool
    route_id: str
    coordinates: List[Dict] = None
    qa_report: Dict = None
    error: str = None


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        pass
    
    def run_import_validate_pipeline(
        self, 
        route_data: Dict,
        start: float = 0,
        end: float = 1000,
        interval: float = 100
    ) -> WorkflowResult:
        """运行完整的导入-验证管道
        
        Steps:
        1. 导入数据
        2. 计算坐标
        3. 自动质检
        4. 生成报告
        """
        try:
            route_id = route_data.get("route_id", "unknown")
            
            # Step 1: 计算坐标
            from core.engine import NeuralSiteEngine
            engine = NeuralSiteEngine(route_id)
            engine.load_from_json(route_data)
            
            coordinates = engine.calculate_range(start, end, interval)
            
            # 转换为字典
            coords_dict = []
            for coord in coordinates:
                coords_dict.append({
                    "station": coord.to_dict()["station"],
                    "x": coord.x,
                    "y": coord.y,
                    "z": coord.z,
                    "azimuth": coord.azimuth
                })
            
            # Step 2: 自动质检
            from core.agents.qa_agent import get_qa_agent
            qa = get_qa_agent()
            report = qa.run_full_validation(route_data, coords_dict)
            
            # 转换为字典
            qa_dict = {
                "report_id": report.report_id,
                "route_id": report.route_id,
                "status": report.status,
                "total_points": report.total_points,
                "issues_count": report.issues_count,
                "summary": report.summary,
                "issues": [
                    {
                        "id": i.issue_id,
                        "severity": i.severity.value,
                        "location": i.location,
                        "type": i.issue_type,
                        "description": i.description,
                        "recommendation": i.recommendation
                    }
                    for i in report.issues
                ]
            }
            
            return WorkflowResult(
                success=True,
                route_id=route_id,
                coordinates=coords_dict,
                qa_report=qa_dict
            )
            
        except Exception as e:
            return WorkflowResult(
                success=False,
                route_id=route_data.get("route_id", "unknown"),
                error=str(e)
            )
    
    def run_full_pipeline(self, route_data: Dict) -> WorkflowResult:
        """运行完整管道
        
        默认计算 K0+000 - K1+200
        """
        return self.run_import_validate_pipeline(
            route_data,
            start=0,
            end=1200,
            interval=50
        )


# 全局实例
_workflow_engine = None


def get_workflow_engine() -> WorkflowEngine:
    """获取工作流引擎"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine


if __name__ == "__main__":
    # Test
    engine = get_workflow_engine()
    
    route_data = {
        "route_id": "demo",
        "horizontal_alignment": [
            {"element_type": "直线", "start_station": "K0+000", "end_station": "K0+500", "azimuth": 45, "x0": 500000, "y0": 3000000},
            {"element_type": "直线", "start_station": "K0+500", "end_station": "K1+200", "azimuth": 45, "x0": 500353, "y0": 3000353}
        ],
        "vertical_alignment": [
            {"station": "K0+000", "elevation": 100, "grade_out": 20},
            {"station": "K1+200", "elevation": 110, "grade_in": 20}
        ]
    }
    
    result = engine.run_full_pipeline(route_data)
    
    print("=== Workflow Result ===")
    print(f"Success: {result.success}")
    print(f"Route: {result.route_id}")
    print(f"Coordinates: {len(result.coordinates) if result.coordinates else 0}")
    print(f"QA Status: {result.qa_report['status'] if result.qa_report else 'N/A'}")
    print(f"Issues: {result.qa_report['issues_count'] if result.qa_report else 0}")
