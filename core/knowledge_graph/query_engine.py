# -*- coding: utf-8 -*-
"""
知识图谱查询引擎
根据问题类型查询解决方案
"""

import sys
sys.path.insert(0, '.')

from storage.graph_db import get_graph_db


class KnowledgeQueryEngine:
    """知识查询引擎"""
    
    def __init__(self):
        self.db = get_graph_db()
    
    def query_solution(self, issue_type: str) -> dict:
        """根据问题类型查询解决方案
        
        Args:
            issue_type: 问题类型，如 "radius_small", "slope_steep"
            
        Returns:
            解决方案字典
        """
        query = """
        MATCH (p:Problem {type: $issue_type})
        OPTIONAL MATCH (p)-[:HAS_SOLUTION]->(s:Solution)
        OPTIONAL MATCH (s)-[:REFERENCES_STANDARD]->(std:Standard)
        OPTIONAL MATCH (s)-[:HAS_MEASURE]->(m:Measure)
        RETURN p.description as problem, 
               s.description as solution,
               s.confidence as confidence,
               std.name as standard,
               collect(m.name) as measures
        """
        
        results = self.db.execute_query(query, {"issue_type": issue_type})
        
        if results:
            return {
                "problem": results[0].get("problem", ""),
                "solution": results[0].get("solution", ""),
                "confidence": results[0].get("confidence", 0),
                "standard": results[0].get("standard", ""),
                "measures": results[0].get("measures", [])
            }
        
        return None
    
    def query_similar_issues(self, location: str) -> list:
        """查询相似位置的历史问题
        
        Args:
            location: 位置，如 "K0+500"
            
        Returns:
            历史问题列表
        """
        query = """
        MATCH (i:Issue)-[:LOCATED_AT]->(l:Location {name: $location})
        OPTIONAL MATCH (i)-[:HAS_SOLUTION]->(s:Solution)
        RETURN i.description as issue, 
               s.description as solution,
               i.severity as severity
        ORDER BY i.timestamp DESC
        LIMIT 5
        """
        
        results = self.db.execute_query(query, {"location": location})
        
        return [
            {
                "issue": r.get("issue", ""),
                "solution": r.get("solution", ""),
                "severity": r.get("severity", "")
            }
            for r in results
        ]
    
    def query_standard(self, standard_code: str) -> dict:
        """查询规范条目
        
        Args:
            standard_code: 规范代码，如 "JTG_D20_7.3"
            
        Returns:
            规范内容
        """
        query = """
        MATCH (s:Standard {code: $code})
        OPTIONAL MATCH (s)-[:HAS_CLAUSE]->(c:Clause)
        RETURN s.name as name, 
               s.code as code,
               c.content as content,
               c.number as clause_number
        """
        
        results = self.db.execute_query(query, {"code": standard_code})
        
        if results:
            return {
                "name": results[0].get("name", ""),
                "code": results[0].get("code", ""),
                "content": results[0].get("content", ""),
                "clause": results[0].get("clause_number", "")
            }
        
        return None


# 全局实例
_query_engine = None


def get_query_engine() -> KnowledgeQueryEngine:
    """获取查询引擎"""
    global _query_engine
    if _query_engine is None:
        _query_engine = KnowledgeQueryEngine()
    return _query_engine


# 预定义解决方案映射
SOLUTION_DATABASE = {
    "radius_zero": {
        "problem": "曲线半径为0",
        "solution": "检查平曲线参数设置，确保半径R > 0",
        "standard": "JTG D20-2017 7.3.1",
        "measures": ["检查输入参数", "核实曲线类型"]
    },
    "radius_too_small": {
        "problem": "曲线半径过小",
        "solution": "增大曲线半径或增设缓和曲线",
        "standard": "JTG D20-2017 7.3.2",
        "measures": [
            "增大半径至规范最小值",
            "设置缓和曲线改善线形",
            "考虑超高横坡补偿"
        ]
    },
    "slope_steep": {
        "problem": "纵坡过陡",
        "solution": "降低纵坡或设置竖曲线",
        "standard": "JTG D20-2017 8.2.1",
        "measures": [
            "降低纵坡坡度",
            "设置竖曲线改善视距",
            "分离式断面设计"
        ]
    },
    "superelevation_exceed": {
        "problem": "超高超限",
        "solution": "调整超高值或采用分离式断面",
        "standard": "JTG D20-2017 8.4.3",
        "measures": [
            "降低超高横坡值",
            "采用分离式路基",
            "增加曲线半径"
        ]
    },
    "spacing_large": {
        "problem": "桩点间距过大",
        "solution": "加密桩点以满足施工精度要求",
        "standard": "JTG D20-2017 附录B",
        "measures": [
            "按20-50m间距加密",
            "增加加桩"
        ]
    }
}


def get_solution(issue_type: str) -> dict:
    """获取问题解决方案
    
    优先查询Neo4j，回退到本地数据库
    """
    # 尝试本地数据库
    if issue_type in SOLUTION_DATABASE:
        return SOLUTION_DATABASE[issue_type]
    
    # 尝试查询图数据库
    try:
        engine = get_query_engine()
        result = engine.query_solution(issue_type)
        if result:
            return result
    except:
        pass
    
    return {
        "problem": issue_type,
        "solution": "请咨询专业工程师",
        "standard": "N/A",
        "measures": ["人工审核"]
    }


if __name__ == "__main__":
    # Test
    for issue in ["radius_small", "slope_steep", "spacing_large"]:
        sol = get_solution(issue)
        print(f"\n=== {issue} ===")
        print(f"Problem: {sol['problem']}")
        print(f"Solution: {sol['solution']}")
        print(f"Standard: {sol['standard']}")
        print(f"Measures: {sol['measures']}")
