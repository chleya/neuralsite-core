# End-to-End Demo: Complete Pipeline

This demo shows the complete NeuralSite Core pipeline:

```
JSON参数 → 几何计算 → LOD2模型 → 碰撞检测 → BIM导出 → 可视化
```

## Quick Start

```bash
# 1. Start API
cd neuralsite-core
python -m uvicorn api.main:app --port 8000

# 2. Start Studio
cd neuralsite-studio
npm run dev
```

## Demo Data

### Input: Road Parameters

```json
{
  "route_id": "demo-highway",
  "design_speed": 80,
  "horizontal_alignment": [
    {
      "element_type": "直线",
      "start_station": "K0+000",
      "end_station": "K0+500",
      "azimuth": 45,
      "x0": 500000,
      "y0": 3000000
    },
    {
      "element_type": "缓和曲线",
      "start_station": "K0+500",
      "end_station": "K0+620",
      "azimuth": 45,
      "x0": 500353.553,
      "y0": 3000353.553,
      "A": 300,
      "radius": 800,
      "direction": "右"
    },
    {
      "element_type": "圆曲线",
      "start_station": "K0+620",
      "end_station": "K1+200",
      "azimuth": 52.5,
      "x0": 500424.264,
      "y0": 3000424.264,
      "radius": 800,
      "center_x": 500424.264,
      "center_y": 3000224.264,
      "direction": "右"
    }
  ],
  "vertical_alignment": [
    {"station": "K0+000", "elevation": 100, "grade_out": 20},
    {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "length": 200},
    {"station": "K1+200", "elevation": 99.5, "grade_in": -15}
  ]
}
```

### Step 1: Calculate Coordinates

```bash
curl -X POST http://localhost:8000/api/v1/calculate/range \
  -H "Content-Type: application/json" \
  -d '{"route_id": "demo", "start": 0, "end": 1200, "interval": 100}'
```

**Response:**
```json
{
  "status": "success",
  "count": 13,
  "data": [
    {"station": "K0+000", "x": 500000, "y": 3000000, "z": 100, "azimuth": 45},
    {"station": "K0+100", "x": 500070.7, "y": 3000070.7, "z": 102, "azimuth": 45},
    ...
  ]
}
```

### Step 2: Create LOD2 Model

```bash
curl -X POST http://localhost:8000/api/v1/lod/demo/abnormal-column
```

### Step 3: Collision Detection

```bash
curl -X POST http://localhost:8000/api/v1/engineering/collision-detection \
  -H "Content-Type: application/json" \
  -d '{
    "component1": {"parameters": {"x": 100, "y": 200, "z": 0, "size": 1}},
    "component2": {"parameters": {"x": 100.5, "y": 200.3, "z": 0.2, "size": 1}},
    "lod_level": 1
  }'
```

**Response:**
```json
{
  "collision_detected": true,
  "status": "COLLISION",
  "lod_level": 1,
  "tolerance": 0.1,
  "distance": {"x": 0.5, "y": 0.3, "z": 0.2, "total": 0.64}
}
```

### Step 4: BIM Export

```bash
curl -X POST http://localhost:8000/api/v1/engineering/generate-bim-model \
  -H "Content-Type: application/json" \
  -d '{
    "component": {
      "componentId": "test-column",
      "type": "AbnormalColumn",
      "parameters": {"width": 0.8, "height": 1.2, "totalHeight": 3.5, "material": "Q345B"}
    },
    "format": "revit"
  }'
```

### Step 5: Visualize in Studio

Open http://localhost:5173

- Switch to "碰撞检测" tab
- Click "重新检测" to trigger API call
- See red collision highlighting in 3D

## Test Results

```
=== Geometry Tests ===
Horizontal Alignment: PASS
  K0+000: X=500000 Y=3000000 Z=100
  K0+500: X=500353 Y=3000353 Z=110
  K1+200: X=500907 Y=3000723 Z=99.5

Vertical Alignment: PASS
  K0+000: Z=100.000
  K0+500: Z=110.000
  K1+200: Z=99.500

Collision Detection: PASS
  LOD0: COLLISION (1.0m tolerance)
  LOD1: COLLISION (0.1m tolerance)
  LOD2: COLLISION (0.01m tolerance)

BIM Export: PASS
  Revit: Family parameters generated
  Tekla: Model object created
  IFC: IfcColumn entity created
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    NeuralSite Core                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐         │
│  │ Parser  │───▶│ Engine  │───▶│  LOD    │         │
│  │ (输入)   │    │ (计算)   │    │ (模型)   │         │
│  └─────────┘    └─────────┘    └─────────┘         │
│       │              │              │               │
│       ▼              ▼              ▼               │
│  ┌─────────────────────────────────────────┐       │
│  │            Neo4j Knowledge Graph        │       │
│  │   (工程实体 + 空间坐标 + 施工关系)        │       │
│  └─────────────────────────────────────────┘       │
│       │              │              │               │
│       ▼              ▼              ▼               │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐         │
│  │ Knowledge│    │Engineering│   │  API   │         │
│  │  Query  │    │ 智能推荐  │    │ 接口   │         │
│  └─────────┘    └─────────┘    └─────────┘         │
│                      │              │               │
└──────────────────────│──────────────│───────────────┘
                       ▼              
              ┌─────────────────┐     
              │ NeuralSite Studio│     
              │  (Three.js)     │     
              │   3D可视化       │     
              └─────────────────┘     
```
