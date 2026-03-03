# -*- coding: utf-8 -*-
"""
Neo4j图数据库
"""

import os
from typing import Dict, List, Optional, Any

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j driver not installed")


def get_neo4j_config():
    """获取Neo4j配置"""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password")
    }


class GraphDatabase:
    """Neo4j图数据库"""
    
    def __init__(self):
        self.driver = None
        if NEO4J_AVAILABLE:
            self._connect()
    
    def _connect(self):
        """连接数据库"""
        config = get_neo4j_config()
        uri = config["uri"]
        user = config["user"]
        password = config["password"]
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            print(f"Connected to Neo4j: {uri}")
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            self.driver = None
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """执行Cypher查询"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Query error: {e}")
            return []
    
    def execute_write(self, query: str, params: Dict = None) -> bool:
        """执行写入"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run(query, params or {})
            return True
        except Exception as e:
            print(f"Write error: {e}")
            return False
    
    def create_node(self, label: str, properties: Dict) -> bool:
        """创建节点"""
        props = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{label} {{{props}}})"
        return self.execute_write(query, properties)
    
    def merge_node(self, label: str, key: str, key_value: Any, properties: Dict) -> bool:
        """合并节点"""
        props = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
        query = f"MERGE (n:{label} {{{key}: $key_value}}) SET {props}"
        params = {**properties, "key_value": key_value}
        return self.execute_write(query, params)
    
    def create_relationship(self, from_label: str, from_key: str, from_value: Any,
                          rel_type: str, to_label: str, to_key: str, to_value: Any) -> bool:
        """创建关系"""
        query = f"""
        MATCH (a:{from_label} {{{from_key}: $from_value}})
        MATCH (b:{to_label} {{{to_key}: $to_value}})
        CREATE (a)-[r:{rel_type}]->(b)
        RETURN r
        """
        return self.execute_write(query, {
            "from_value": from_value,
            "to_value": to_value
        })
    
    def find_node(self, label: str, key: str, value: Any) -> Optional[Dict]:
        """查找节点"""
        query = f"MATCH (n:{label} {{{key}: $value}}) RETURN n"
        results = self.execute_query(query, {"value": value})
        return results[0].get("n") if results else None
    
    def find_related(self, label: str, key: str, value: Any, rel_type: str) -> List[Dict]:
        """查找关联节点"""
        query = f"""
        MATCH (n:{label} {{{key}: $value}})-[r:{rel_type}]->(related)
        RETURN related
        """
        return self.execute_query(query, {"value": value})


# 全局实例
_graph_db = None


def get_graph_db() -> GraphDatabase:
    """获取图数据库实例"""
    global _graph_db
    if _graph_db is None:
        _graph_db = GraphDatabase()
    return _graph_db


if __name__ == "__main__":
    # 测试
    db = GraphDatabase()
    if db.driver:
        # 测试查询
        result = db.execute_query("RETURN 1 as test")
        print(f"Neo4j test: {result}")
        db.close()
    else:
        print("Neo4j not available")
