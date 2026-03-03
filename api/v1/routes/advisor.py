# -*- coding: utf-8 -*-
"""
智能顾问API
自然语言问答接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

import sys
sys.path.insert(0, '.')

from core.knowledge_graph.query_engine import get_solution, SOLUTION_DATABASE
from core.agents.qa_agent import get_qa_agent


router = APIRouter(prefix="/api/v1/advisor", tags=["智能顾问"])


class QuestionRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="问题内容")
    location: Optional[str] = Field(default=None, description="相关位置")


@router.post("/ask")
async def ask_advisor(request: QuestionRequest):
    """智能问答
    
    用户提问，系统从知识图谱中检索答案
    支持的问题类型：
    - "半径太小怎么办"
    - "K0+500有什么问题"
    - "纵坡超限怎么解决"
    """
    question = request.question.lower()
    
    # 意图识别
    intent = None
    params = {}
    
    # 提取位置
    import re
    location_match = re.search(r'k\d+\+\d+', question)
    if location_match:
        params["location"] = location_match.group()
    
    # 问题类型匹配
    if "半径" in question or "radius" in question:
        if "0" in question or "为零" in question:
            intent = "radius_zero"
        else:
            intent = "radius_too_small"
    elif "纵坡" in question or "坡度" in question or "slope" in question:
        intent = "slope_steep"
    elif "超高" in question or "superelevation" in question:
        intent = "superelevation_exceed"
    elif "间距" in question or "间距" in question or "spacing" in question:
        intent = "spacing_large"
    elif "碰撞" in question or "collision" in question:
        intent = "collision"
    
    # 如果识别到问题类型，查询解决方案
    if intent:
        solution = get_solution(intent)
        
        return {
            "status": "success",
            "intent": intent,
            "question": request.question,
            "answer": solution.get("solution", "请咨询专业工程师"),
            "standard": solution.get("standard", "N/A"),
            "measures": solution.get("measures", []),
            "location": params.get("location")
        }
    
    # 默认回答
    return {
        "status": "unknown",
        "question": request.question,
        "answer": "我理解您的问题，但需要更多上下文。请具体说明是关于半径、纵坡、超高还是其他问题？"
    }


@router.get("/solutions")
async def list_solutions():
    """列出所有可用的解决方案"""
    return {
        "solutions": [
            {
                "id": key,
                "problem": val["problem"],
                "solution": val["solution"],
                "standard": val["standard"]
            }
            for key, val in SOLUTION_DATABASE.items()
        ]
    }


@router.get("/standards")
async def list_standards():
    """列出设计规范"""
    return {
        "standards": [
            {"code": "JTG D20-2017 7.3.1", "name": "公路路线设计规范 - 曲线半径"},
            {"code": "JTG D20-2017 8.2.1", "name": "公路路线设计规范 - 纵坡"},
            {"code": "JTG D20-2017 8.4.3", "name": "公路路线设计规范 - 超高"},
            {"code": "JTG D20-2017 附录B", "name": "公路路线设计规范 - 桩点间距"}
        ]
    }


@router.post("/demo")
async def demo_advisor():
    """演示：问答示例"""
    questions = [
        "曲线半径太小怎么办?",
        "纵坡超限怎么处理?",
        "超高超限怎么解决?",
        "桩点间距过大可以吗?"
    ]
    
    results = []
    for q in questions:
        req = QuestionRequest(question=q)
        resp = await ask_advisor(req)
        results.append({
            "question": q,
            "answer": resp["answer"],
            "standard": resp["standard"]
        })
    
    return {
        "demo": results
    }
