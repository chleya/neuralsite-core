# NeuralSite Core

🛣️ 公路参数化几何计算引擎

## 核心理念

- **AI原生开发**: 不是"喂代码给AI"，而是"让AI从零编写系统"
- **离线优先**: 所有计算本地运行
- **参数化内核**: 基于JTG规范的数学公式

## 项目结构

```
neuralsite_core/
├── core/                   # 核心引擎
│   ├── geometry/         # 几何计算
│   │   ├── horizontal.py  # 平曲线
│   │   ├── vertical.py   # 竖曲线
│   │   └── cross_section.py # 横断面
│   └── engine.py         # 引擎主入口
│
├── agents/               # AI智能体
├── api/                  # FastAPI接口
├── storage/              # 离线存储
└── utils/               # 工具库
```

## 使用

```python
from core import NeuralSiteEngine

engine = NeuralSiteEngine("ROUTE001")
engine.load_from_json(data)

# 计算坐标
coord = engine.get_coordinate(500)
print(coord.to_dict())
```

## 规范参考

- JTG D20-2017《公路路线设计规范》
- JTG/T 2420-2021《公路工程信息模型应用统一标准》

## License

MIT
