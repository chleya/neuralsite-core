# NeuralSite Core

🛣️ 公路工程参数化建模系统

基于AI-Native开发理念，构建完全离线、参数化、可扩展的路基数字化内核。

## 核心特性

- **几何内核**: 平曲线、竖曲线、横断面计算
- **知识图谱**: Neo4j图数据库存储工程实体关系
- **LOD分层**: 支持LOD0(米级)/LOD1(分米级)/LOD2(厘米级)精度
- **异形构件**: 参数化主体 + 局部细节补丁表示
- **工程智能**: 施工工艺推荐、碰撞检测、BIM导出

## 架构

```
NeuralSite Core/
├── core/
│   ├── geometry/       # 几何计算引擎
│   ├── models/         # LOD数据模型
│   ├── knowledge_graph/ # Neo4j图谱
│   └── engineering/    # 工程智能
├── api/v1/routes/
│   ├── calculate.py    # 坐标计算API
│   ├── knowledge.py   # 知识查询API
│   ├── lod.py         # LOD管理API
│   └── engineering.py # 工程智能API
└── storage/           # SQLite + Neo4j
```

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 运行API

```bash
python -m uvicorn api.main:app --reload
```

访问 http://localhost:8000/docs 查看Swagger文档

## API文档

### 1. 坐标计算

```bash
# 单点计算
POST /api/v1/calculate
{"route_id": "demo", "station": 500}

# 批量计算
POST /api/v1/calculate/range
{"route_id": "demo", "start": 0, "end": 1000, "interval": 100}
```

### 2. 知识图谱

```bash
# 初始化
POST /api/v1/knowledge/init

# 查询
POST /api/v1/knowledge/query
{"question": "K0+500的设计标高是多少"}

# 创建实体
POST /api/v1/knowledge/entity
{
  "project": "项目1",
  "drawing": "路线平面图",
  "drawing_type": "平面图",
  "feature_id": "K0+500",
  "feature_type": "路基",
  "chainage": "K0+500",
  "x": 500353, "y": 3000353, "z": 110
}
```

### 3. LOD数据

```bash
# 演示：创建异形柱
POST /api/v1/lod/demo/abnormal-column

# 演示：创建路基
POST /api/v1/lod/demo/subgrade
```

### 4. 工程智能

```bash
# 施工工艺推荐
POST /api/v1/engineering/recommend-construction
{
  "component_type": "AbnormalColumn",
  "material": "Q345B",
  "complexity": "high"
}

# 碰撞检测 (LOD0/1/2)
POST /api/v1/engineering/collision-detection
{
  "component1": {"parameters": {"x": 100, "y": 200, "z": 0, "size": 1}},
  "component2": {"parameters": {"x": 100.5, "y": 200.3, "z": 0.2, "size": 1}},
  "lod_level": 1
}

# BIM导出 (revit/tekla/ifc)
POST /api/v1/engineering/generate-bim-model
{
  "component": {"componentId": "test", "type": "AbnormalColumn", "parameters": {...}},
  "format": "revit"
}
```

## 测试

```bash
python tests/test_engineering.py
```

## 技术栈

- **后端**: Python, FastAPI
- **数据库**: SQLite, Neo4j
- **3D渲染**: Three.js (Studio)
- **协议**: REST API

## 许可证

MIT
