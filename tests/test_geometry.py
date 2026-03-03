# -*- coding: utf-8 -*-
"""
Geometry Kernel Tests
Test horizontal curve, vertical curve, cross section calculations
"""

import sys
sys.path.insert(0, '.')

from core.geometry.horizontal import LineElement, CircularCurveElement, SpiralCurveElement, HorizontalAlignment
from core.geometry.vertical import VerticalCurveElement, VerticalAlignment
from core.geometry.cross_section import CrossSectionTemplate, SuperElevation


def test_horizontal_alignment():
    """Test horizontal curve calculation"""
    print("=== Test: Horizontal Alignment ===")
    
    # Create horizontal curve: line + spiral + circular
    elements = [
        # Line: K0+000 ~ K0+500
        LineElement(
            start_station=0,
            end_station=500,
            azimuth=45,  # 45 degrees
            x0=500000,
            y0=3000000
        ),
        # Spiral: K0+500 ~ K0+620
        SpiralCurveElement(
            start_station=500,
            end_station=620,
            azimuth=45,
            x0=500353.553,
            y0=3000353.553,
            A=300,  # parameter A
            radius=800,  # radius
            direction='right'
        ),
        # Circular: K0+620 ~ K1+200
        CircularCurveElement(
            start_station=620,
            end_station=1200,
            radius=800,
            azimuth=52.5,
            x0=500424.264,
            y0=3000424.264,
            center_x=500424.264,
            center_y=3000224.264,
            direction='right'
        )
    ]
    
    alignment = HorizontalAlignment()
    for elem in elements:
        alignment.add_element(elem)
    
    # Test coordinates at various stations
    test_stations = [0, 250, 500, 560, 620, 800, 1000, 1200]
    
    for s in test_stations:
        x, y, azimuth = alignment.get_coordinate(s)
        print("K{:.3f}: X={:.3f} Y={:.3f} Az={:.2f}".format(
            s/1000, x, y, azimuth
        ))
    
    # Verify: K0+500 should be at end of line
    x_500, y_500, _ = alignment.get_coordinate(500)
    expected_x = 500000 + 500 * 0.707107  # cos(45)
    expected_y = 3000000 + 500 * 0.707107  # sin(45)
    
    assert abs(x_500 - expected_x) < 0.01, "X coordinate error"
    assert abs(y_500 - expected_y) < 0.01, "Y coordinate error"
    print("[OK] K0+500 coordinate verified")
    
    print("PASS: Horizontal Alignment\n")


def test_vertical_alignment():
    """Test vertical curve calculation"""
    print("=== Test: Vertical Alignment ===")
    
    # Create vertical curve
    curves = [
        # VPI1: K0+000 elevation 100, grade +2%
        VerticalCurveElement(
            station=0,
            elevation=100,
            grade_in=0,
            grade_out=20
        ),
        
        # VPI2: K0+500 elevation 110, grade -1.5%
        VerticalCurveElement(
            station=500,
            elevation=110,
            grade_in=20,
            grade_out=-15,
            length=200
        ),
        
        # VPI3: K1+200 elevation 99.5
        VerticalCurveElement(
            station=1200,
            elevation=99.5,
            grade_in=-15,
            grade_out=0
        )
    ]
    
    alignment = VerticalAlignment()
    for curve in curves:
        alignment.add_element(curve)
    
    # Test elevation at various stations
    test_stations = [0, 100, 250, 400, 500, 600, 800, 1000, 1200]
    
    for s in test_stations:
        z = alignment.get_elevation(s)
        print("K{:.3f}: Z={:.3f}".format(s/1000, z))
    
    # Verify: K0+500 should be at elevation 110m
    z_500 = alignment.get_elevation(500)
    assert abs(z_500 - 110) < 0.01, "K0+500 elevation error"
    print("[OK] K0+500 elevation verified")
    
    print("PASS: Vertical Alignment\n")


def test_super_elevation():
    """Test super elevation transition"""
    print("=== Test: Super Elevation ===")
    
    # Create super elevation
    super_elev = SuperElevation(
        max_rate=5.0,  # max 5%
        rotation_axis="中",
        transition_type="线性"
    )
    
    # Test values
    print("max_rate: {}%".format(super_elev.max_rate))
    print("rotation_axis: {}".format(super_elev.rotation_axis))
    print("transition_type: {}".format(super_elev.transition_type))
    
    assert super_elev.max_rate == 5.0, "Max rate error"
    assert super_elev.rotation_axis == "中", "Rotation axis error"
    
    print("PASS: Super Elevation\n")


def test_cross_section():
    """Test cross section calculation"""
    print("=== Test: Cross Section ===")
    
    # Create cross section template
    cs_template = CrossSectionTemplate(
        width=26,  # road width
        lane_width=3.75,
        lanes=4,
        shoulder_width=2.5
    )
    
    # Use calculator
    from core.geometry.cross_section import CrossSectionCalculator
    cs_calc = CrossSectionCalculator(cs_template)
    
    # Test section at various stations
    stations = [0, 500, 1000]
    
    for s in stations:
        result = cs_calc.calculate(s)
        print("K{:.3f}: width={}m, half_width={}".format(
            s/1000, cs_template.width, result['half_width']
        ))
    
    print("PASS: Cross Section\n")


def test_full_alignment():
    """Test full alignment calculation"""
    print("=== Test: Full Alignment ===")
    
    # Create horizontal alignment
    h_elements = [
        LineElement(0, 500, 45, 500000, 3000000),
        SpiralCurveElement(500, 620, 45, 500353.553, 3000353.553, A=300, radius=800, direction='right'),
        CircularCurveElement(620, 1200, 800, 52.5, 500424.264, 3000424.264, center_x=500424.264, center_y=3000224.264, direction='right')
    ]
    h_align = HorizontalAlignment()
    for elem in h_elements:
        h_align.add_element(elem)
    
    # Create vertical alignment
    v_curves = [
        VerticalCurveElement(station=0, elevation=100, grade_in=0, grade_out=20),
        VerticalCurveElement(station=500, elevation=110, grade_in=20, grade_out=-15, length=200),
        VerticalCurveElement(station=1200, elevation=99.5, grade_in=-15, grade_out=0)
    ]
    v_align = VerticalAlignment()
    for curve in v_curves:
        v_align.add_element(curve)
    
    # Create cross section
    cs = CrossSectionTemplate(26, 3.75, 4, 2.5)
    
    # Calculate coordinates K0+000 ~ K1+200
    results = []
    for s in range(0, 1201, 200):
        x, y, azimuth = h_align.get_coordinate(s)
        z = v_align.get_elevation(s)
        
        results.append({
            "station": s,
            "x": x,
            "y": y,
            "z": z,
            "azimuth": azimuth
        })
        
        print("K{:.3f}: X={:.2f} Y={:.2f} Z={:.2f} Az={:.1f}".format(
            s/1000, x, y, z, azimuth
        ))
    
    # Verify results - K0+400 should have elevation close to 108
    assert len(results) == 7, "Should have 7 test points"
    assert abs(results[2]["z"] - 108) < 0.1, "K0+400 elevation verification"
    
    print("[OK] Full alignment verified")
    print("PASS: Full Alignment\n")


def run_all_tests():
    """Run all geometry tests"""
    print("\n" + "="*50)
    print("NeuralSite Core - Geometry Tests")
    print("="*50 + "\n")
    
    test_horizontal_alignment()
    test_vertical_alignment()
    test_super_elevation()
    test_cross_section()
    test_full_alignment()
    
    print("="*50)
    print("ALL GEOMETRY TESTS PASSED!")
    print("="*50 + "\n")


if __name__ == "__main__":
    run_all_tests()
