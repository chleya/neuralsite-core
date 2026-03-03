# NeuralSite 项目结构定义

## 项目骨架

```
NeuralSite-Core/
├── core/                     # 【核心几何引擎】
│   ├── geometry/           # 几何计算模块
│   │   ├── horizontal.py    # 平曲线计算 (直线/缓和/圆)
│   │   ├── vertical.py      # 纵断面计算 (抛物线)
│   │   └── cross_section.py # 横断面扫掠
│   └── engine.py          # 主引擎:组合上述模块
│
├── api/                     # 【API接口层】
│   ├── v1/                # API版本控制
│   │   ├── routes/        # 路由文件
│   │   │   ├── calculate.py # 计算坐标接口
│   │   │   └── parse.py    # 解析图纸接口
│   │   └── main.py        # FastAPI入口
│   └── schemas/           # 数据模型
│       └── models.py      # Pydantic模型定义
│
├── agents/                  # 【AI智能体】
│   ├── parser.py         # 负责从文本/CAD中提取参数
│   └── planner.py        # 负责施工调度逻辑
│
├── storage/                 # 【存储层】
│   ├── db/               # SQLite数据库
│   └── cache/            # 缓存
│
├── utils/                  # 【工具库】
│   └── units.py         # 单位转换工具
│
├── config.py              # 配置文件
├── requirements.txt       # 依赖列表
└── README.md             # 项目说明
```

## 模块说明

| 模块 | 职责 |
|------|------|
| core/geometry | 数学公式计算 (与业务无关) |
| core/engine | 业务逻辑组装 |
| api | HTTP接口 |
| agents | AI智能逻辑 |
| storage | 数据持久化 |
| utils | 通用工具 |
