# -*- coding: utf-8 -*-
"""
NeuralSite Core CLI
命令行入口
"""

import click
import sys
import os
import json
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import NeuralSiteEngine
from agents.parser import DesignParser
from storage.manager import get_storage, init_sample
from output.model.generator import ModelGenerator, EarthworkCalculator


@click.group()
def cli():
    """NeuralSite Core - 公路参数化建模系统"""
    pass


@cli.command()
@click.argument('text')
@click.option('--output', '-o', help='输出JSON文件')
def parse(text, output):
    """解析工程文本参数"""
    click.echo(f"[Parse] {text}")
    
    parser = DesignParser()
    result = parser.parse_text(text)
    
    click.echo(f"[OK] 提取参数:")
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        click.echo(f"[Saved] {output}")


@cli.command()
@click.option('--start', default=0, help='起始桩号(m)')
@click.option('--end', default=2000, help='结束桩号(m)')
@click.option('--interval', default=100, help='间隔(m)')
@click.option('--lod', default='LOD1', help='LOD级别')
@click.option('--output', '-o', help='输出JSON文件')
def calculate(start, end, interval, lod, output):
    """计算坐标"""
    click.echo(f"[Calculate] {start}m - {end}m, interval={interval}m")
    
    # 创建引擎并加载示例数据
    engine = NeuralSiteEngine("CLI_ROUTE")
    sample_data = {
        "route_id": "CLI_ROUTE",
        "design_speed": 80,
        "horizontal_alignment": [
            {"element_type": "直线", "start_station": "K0+000", "end_station": "K0+500",
             "azimuth": 45, "x0": 500000, "y0": 3000000},
            {"element_type": "缓和曲线", "start_station": "K0+500", "end_station": "K0+600",
             "azimuth": 45, "x0": 500353.553, "y0": 3000353.553, "A": 300, "R": 800, "direction": "右"},
            {"element_type": "圆曲线", "start_station": "K0+600", "end_station": "K1+200",
             "azimuth": 45, "x0": 500424.264, "y0": 3000424.264, "R": 800,
             "cx": 500424.264, "cy": 3000224.264, "direction": "右"}
        ],
        "vertical_alignment": [
            {"station": "K0+000", "elevation": 100, "grade_out": 20},
            {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "length": 200},
            {"station": "K1+200", "elevation": 99.5, "grade_in": -15}
        ],
        "cross_section_template": {"width": 26, "lanes": 4}
    }
    engine.load_from_json(sample_data)
    
    # 计算
    results = engine.calculate_range(start, end, interval)
    
    click.echo(f"[OK] 计算完成: {len(results)} 个点")
    
    for r in results[:5]:
        click.echo(f"  {r['station']}: X={r['x']} Y={r['y']} Z={r['z']}")
    
    if len(results) > 5:
        click.echo(f"  ... 共 {len(results)} 个点")
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        click.echo(f"[Saved] {output}")


@cli.command()
@click.option('--start', default=0, help='起始桩号(m)')
@click.option('--end', default=1000, help='结束桩号(m)')
@click.option('--interval', default=50, help='间隔(m)')
@click.option('--width', default=10, help='道路宽度')
@click.option('--output', '-o', default='model.obj', help='输出OBJ文件')
def model(start, end, interval, width, output):
    """生成3D模型"""
    click.echo(f"[Model] {start}m - {end}m, width={width}m")
    
    # 计算坐标
    engine = NeuralSiteEngine("MODEL_ROUTE")
    sample_data = {
        "route_id": "MODEL_ROUTE",
        "design_speed": 80,
        "horizontal_alignment": [
            {"element_type": "直线", "start_station": "K0+000", "end_station": "K0+500",
             "azimuth": 45, "x0": 500000, "y0": 3000000},
            {"element_type": "缓和曲线", "start_station": "K0+500", "end_station": "K0+600",
             "azimuth": 45, "x0": 500353.553, "y0": 3000353.553, "A": 300, "R": 800, "direction": "右"},
            {"element_type": "圆曲线", "start_station": "K0+600", "end_station": "K1+200",
             "azimuth": 45, "x0": 500424.264, "y0": 3000424.264, "R": 800,
             "cx": 500424.264, "cy": 3000224.264, "direction": "右"}
        ],
        "vertical_alignment": [
            {"station": "K0+000", "elevation": 100, "grade_out": 20},
            {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "length": 200},
            {"station": "K1+200", "elevation": 99.5, "grade_in": -15}
        ],
        "cross_section_template": {"width": 26}
    }
    engine.load_from_json(sample_data)
    
    coords = engine.calculate_range(start, end, interval)
    
    # 生成模型
    gen = ModelGenerator()
    gen.generate_mesh(coords, width=width)
    
    gen.save_obj(output)
    click.echo(f"[OK] 模型已保存: {output}")
    click.echo(f"  顶点数: {len(gen.vertices)}")
    click.echo(f"  面数: {len(gen.faces)}")


@cli.command()
def init():
    """初始化数据库"""
    click.echo("[Init] 初始化数据库...")
    init_sample()
    click.echo("[OK] 初始化完成")


@cli.command()
def projects():
    """列出项目"""
    click.echo("[Projects]")
    storage = get_storage()
    
    for p in storage.list_projects():
        click.echo(f"  - {p.name} (ID: {p.id})")


@cli.command()
@click.argument('project_name')
def info(project_name):
    """查看项目详情"""
    click.echo(f"[Info] {project_name}")
    
    storage = get_storage()
    project = storage.get_project(name=project_name)
    
    if not project:
        click.echo("[Error] 项目不存在")
        return
    
    click.echo(f"  名称: {project.name}")
    click.echo(f"  描述: {project.description}")
    click.echo(f"  创建: {project.created_at}")
    
    routes = storage.list_routes(project.id)
    click.echo(f"  路线: {len(routes)} 条")
    
    for r in routes:
        click.echo(f"    - {r.name} (K{r.start_station//1000}+{r.start_station%1000:03d} - K{r.end_station//1000}+{r.end_station%1000:03d})")


@cli.command()
def demo():
    """运行演示"""
    click.echo("=== NeuralSite Core Demo ===\n")
    
    # 1. 解析
    click.echo("1. 解析工程文本...")
    parser = DesignParser()
    text = "主线: R=800, LS=120, K0+000"
    result = parser.parse_text(text)
    click.echo(f"   输入: {text}")
    click.echo(f"   提取: {len(result.get('horizontal', []))} 个平曲线元素")
    
    # 2. 计算
    click.echo("\n2. 计算坐标...")
    engine = NeuralSiteEngine("DEMO")
    engine.load_from_json(parser.to_engine_format())
    coord = engine.get_coordinate(500)
    click.echo(f"   K0+500: X={coord.x:.2f} Y={coord.y:.2f} Z={coord.z:.2f}")
    
    # 3. 横断面
    click.echo("\n3. 计算横断面...")
    cs = engine.calculate_cross_section(500)
    click.echo(f"   中心: ({cs['center'][0]:.2f}, {cs['center'][1]:.2f}, {cs['center'][2]:.2f})")
    
    # 4. 模型
    click.echo("\n4. 生成3D模型...")
    coords = engine.calculate_range(0, 500, 100)
    gen = ModelGenerator()
    gen.generate_mesh(coords, width=10)
    click.echo(f"   顶点数: {len(gen.vertices)}, 面数: {len(gen.faces)}")
    
    # 5. 土方
    click.echo("\n5. 计算土方量...")
    calc = EarthworkCalculator()
    calc.add_section(0, 100)
    calc.add_section(500, 120)
    volume = calc.calculate_volume()
    click.echo(f"   填方: {volume['fill']:.0f} m³")
    click.echo(f"   挖方: {volume['cut']:.0f} m³")
    
    click.echo("\n=== Demo Complete ===")


if __name__ == '__main__':
    cli()
