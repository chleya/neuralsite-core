# -*- coding: utf-8 -*-
"""
Excel Road Data Importer
Parse design tables from Excel to NeuralSite format
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import io


@dataclass
class RoadParameter:
    """道路参数"""
    station: str           # 桩号
    x: float              # X坐标
    y: float              # Y坐标
    z: float              # 高程
    azimuth: float        # 方位角
    radius: Optional[float] = None  # 半径(平曲线)
    A: Optional[float] = None        # 缓和曲线参数


class ExcelRoadImporter:
    """Excel道路数据导入器"""
    
    def __init__(self):
        self.data = []
    
    def parse_station_coordinate_table(self, df: pd.DataFrame) -> List[RoadParameter]:
        """解析逐桩坐标表
        
        Expected columns: 桩号, X, Y, Z (or 经度, 纬度, 高程)
        """
        # 标准化列名
        columns = df.columns.tolist()
        
        # 找关键列
        station_col = self._find_column(columns, ['桩号', 'Station', '里程', 'STATION'])
        x_col = self._find_column(columns, ['X', 'x', 'Easting', '经度'])
        y_col = self._find_column(columns, ['Y', 'y', 'Northing', '纬度'])
        z_col = self._find_column(columns, ['Z', 'z', '高程', 'Elevation', '标高'])
        
        if not all([station_col, x_col, y_col]):
            raise ValueError(f"Cannot find required columns. Found: {columns}")
        
        results = []
        
        for _, row in df.iterrows():
            station = str(row[station_col])
            
            try:
                x = float(row[x_col])
                y = float(row[y_col])
                z = float(row[z_col]) if z_col else 0.0
                
                # 计算方位角
                azimuth = self._calculate_azimuth(y, x)
                
                results.append(RoadParameter(
                    station=station,
                    x=x,
                    y=y,
                    z=z,
                    azimuth=azimuth
                ))
            except (ValueError, TypeError):
                continue
        
        return results
    
    def parse_horizontal_alignment(self, df: pd.DataFrame) -> List[Dict]:
        """解析平曲线参数表
        
        Expected columns: 交点号, 桩号, 半径R, 缓和曲线A, 方位角
        """
        columns = df.columns.tolist()
        
        # 找关键列
        jd_col = self._find_column(columns, ['交点号', 'JD', 'Point', '点号'])
        station_col = self._find_column(columns, ['桩号', 'Station', '里程'])
        r_col = self._find_column(columns, ['半径', 'R', 'Radius'])
        a_col = self._find_column(columns, ['缓和曲线', 'A', 'Ls', 'LS'])
        azimuth_col = self._find_column(columns, ['方位角', 'Azimuth', '方向'])
        
        if not station_col:
            raise ValueError("Cannot find station column")
        
        elements = []
        
        for _, row in df.iterrows():
            station = str(row[station_col])
            
            element = {
                "element_type": "圆曲线",  # 默认
                "start_station": station,
                "end_station": station,
                "azimuth": float(row[azimuth_col]) if azimuth_col else 0,
                "x0": 0,
                "y0": 0
            }
            
            if r_col and pd.notna(row[r_col]):
                element["radius"] = float(row[r_col])
            
            if a_col and pd.notna(row[a_col]):
                element["A"] = float(row[a_col])
                element["element_type"] = "缓和曲线"
            
            elements.append(element)
        
        return elements
    
    def parse_vertical_alignment(self, df: pd.DataFrame) -> List[Dict]:
        """解析竖曲线参数表
        
        Expected columns: 变坡点桩号, 标高, 坡度
        """
        columns = df.columns.tolist()
        
        station_col = self._find_column(columns, ['桩号', 'Station', '里程', 'VPI'])
        elev_col = self._find_column(columns, ['标高', '高程', 'Elevation', 'Z'])
        grade_col = self._find_column(columns, ['坡度', 'Grade', 'i', '坡度‰'])
        
        if not station_col or not elev_col:
            raise ValueError("Cannot find required columns")
        
        vpi_points = []
        
        for _, row in df.iterrows():
            station = str(row[station_col])
            elevation = float(row[elev_col])
            
            point = {
                "station": station,
                "elevation": elevation,
                "grade_out": float(row[grade_col]) if grade_col else 0
            }
            
            vpi_points.append(point)
        
        # 处理坡度连接
        for i in range(len(vpi_points) - 1):
            vpi_points[i]["grade_in"] = vpi_points[i].get("grade_out", 0)
            vpi_points[i+1]["grade_in"] = vpi_points[i].get("grade_out", 0)
        
        return vpi_points
    
    def _find_column(self, columns: List[str], candidates: List[str]) -> Optional[str]:
        """查找匹配的列名"""
        for cand in candidates:
            for col in columns:
                if cand.lower() in col.lower():
                    return col
        return None
    
    def _calculate_azimuth(self, y: float, x: float) -> float:
        """计算方位角"""
        import math
        if x == 0:
            return 0
        angle = math.degrees(math.atan2(y, x))
        return angle if angle >= 0 else angle + 360
    
    def to_neuralsite_format(self, horizontal: List[Dict], vertical: List[Dict]) -> Dict:
        """转换为NeuralSite格式"""
        return {
            "route_id": "imported_road",
            "design_speed": 80,
            "horizontal_alignment": horizontal,
            "vertical_alignment": vertical
        }


def parse_excel_file(file_content: bytes) -> Dict:
    """解析Excel文件，返回NeuralSite格式
    
    Args:
        file_content: Excel文件二进制内容
        
    Returns:
        NeuralSite格式的路线参数
    """
    # 尝试读取所有sheet
    excel_file = pd.ExcelFile(io.BytesIO(file_content))
    
    importer = ExcelRoadImporter()
    result = {
        "route_id": "imported_road",
        "horizontal_alignment": [],
        "vertical_alignment": []
    }
    
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # 检测表格类型
        columns = [c.lower() for c in df.columns.tolist()]
        
        if 'x' in columns and 'y' in columns:
            # 逐桩坐标表
            coords = importer.parse_station_coordinate_table(df)
            # 转换为平曲线元素(简化处理)
            result["horizontal_alignment"] = _coords_to_alignment(coords)
        
        elif '半径' in [c.lower() for c in df.columns] or 'r' in [c.lower() for c in df.columns]:
            # 平曲线参数表
            result["horizontal_alignment"] = importer.parse_horizontal_alignment(df)
        
        elif '标高' in [c.lower() for c in df.columns] or '高程' in [c.lower() for c in df.columns]:
            # 竖曲线参数表
            result["vertical_alignment"] = importer.parse_vertical_alignment(df)
    
    return result


def _coords_to_alignment(coords: List[RoadParameter]) -> List[Dict]:
    """将坐标点转换为线元"""
    if not coords:
        return []
    
    elements = []
    
    for i, coord in enumerate(coords):
        if i == 0:
            # 起点
            elements.append({
                "element_type": "直线",
                "start_station": coord.station,
                "end_station": coord.station,
                "azimuth": coord.azimuth,
                "x0": coord.x,
                "y0": coord.y
            })
        else:
            # 后续点
            elements.append({
                "element_type": "直线",
                "start_station": coords[i-1].station,
                "end_station": coord.station,
                "azimuth": coord.azimuth,
                "x0": coords[i-1].x,
                "y0": coords[i-1].y
            })
    
    return elements


# Demo data for testing
DEMO_EXCEL_DATA = """桩号,X,Y,Z
K0+000,500000,3000000,100
K0+100,500070.71,3000070.71,102
K0+200,500141.42,3000141.42,104
K0+300,500212.13,3000212.13,106
K0+400,500282.84,3000282.84,108
K0+500,500353.55,3000353.55,110
K0+600,500424.26,3000424.26,108
K0+700,500565.69,3000506.64,104
K0+800,500707.11,3000585.79,102
K0+900,500848.55,3000661.22,100
K1+000,500990.00,3000733.00,99
K1+100,501131.47,3000801.15,98
K1+200,501272.95,3002865.67,97
"""


if __name__ == "__main__":
    # Test
    import sys
    sys.path.insert(0, '.')
    
    from core.geometry.horizontal import LineElement, HorizontalAlignment
    from core.geometry.vertical import VerticalCurveElement, VerticalAlignment
    
    # Create sample data
    result = parse_excel_file(DEMO_EXCEL_DATA.encode())
    print("Parsed result:")
    print(result)
