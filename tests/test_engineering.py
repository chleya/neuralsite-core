# -*- coding: utf-8 -*-
"""
Engineering Intelligence Tests
"""

import sys
sys.path.insert(0, '.')

from core.engineering.engine import (
    EngineeringIntelligence,
    get_engineering_intel,
    ConstructionMethod
)


def test_construction_recommendation():
    print("=== Test: Construction Recommendation ===")
    
    engine = get_engineering_intel()
    
    # Test 1: Abnormal column
    recs = engine.recommend_construction_method(
        component_type="AbnormalColumn",
        material="Q345B",
        complexity="high"
    )
    
    assert len(recs) > 0, "Should return recommendations"
    assert recs[0].method == "数控切割", "First should be CNC cutting"
    assert recs[0].confidence > 0.9, "Confidence should be >90%"
    print("[OK] Abnormal column: {} ({:.0%})".format(recs[0].method, recs[0].confidence))
    
    # Test 2: Prefab
    recs = engine.recommend_construction_method(
        component_type="PrefabBeam",
        material="C40",
        complexity="medium"
    )
    print("[OK] Prefab: {}".format(recs[0].method))
    
    # Test 3: Concrete
    recs = engine.recommend_construction_method(
        component_type="Wall",
        material="C30",
        complexity="low"
    )
    print("[OK] Concrete: {}".format(recs[0].method))
    
    print("PASS: Construction Recommendation\n")


def test_collision_detection():
    print("=== Test: Collision Detection ===")
    
    engine = get_engineering_intel()
    
    # Two close components
    comp1 = {"parameters": {"x": 100.0, "y": 200.0, "z": 0.0, "size": 1.0}}
    comp2 = {"parameters": {"x": 100.5, "y": 200.3, "z": 0.2, "size": 1.0}}
    
    # LOD0
    result = engine.detect_collision(comp1, comp2, lod_level=0)
    assert result["collision_detected"] == True
    print("[OK] LOD0: {}, tolerance: {}m".format(result['status'], result['tolerance']))
    
    # LOD1
    result = engine.detect_collision(comp1, comp2, lod_level=1)
    print("[OK] LOD1: {}, tolerance: {}m".format(result['status'], result['tolerance']))
    
    # LOD2
    result = engine.detect_collision(comp1, comp2, lod_level=2)
    print("[OK] LOD2: {}, tolerance: {}m".format(result['status'], result['tolerance']))
    
    # No collision
    comp3 = {"parameters": {"x": 100.0, "y": 200.0, "z": 0.0, "size": 0.5}}
    comp4 = {"parameters": {"x": 200.0, "y": 300.0, "z": 10.0, "size": 0.5}}
    
    result = engine.detect_collision(comp3, comp4, lod_level=1)
    assert result["collision_detected"] == False
    print("[OK] No collision: {}".format(result['status']))
    
    print("PASS: Collision Detection\n")


def test_bim_export():
    print("=== Test: BIM Export ===")
    
    engine = get_engineering_intel()
    
    component = {
        "componentId": "test-column-001",
        "type": "AbnormalColumn",
        "description": "Test column",
        "parameters": {
            "width": 0.8,
            "height": 1.2,
            "totalHeight": 3.5,
            "material": "Q345B",
            "slope": 0.05,
            "cornerRadius": 0.1
        }
    }
    
    # Revit
    revit = engine.export_to_bim_format(component, "revit")
    assert "parameters" in revit
    print("[OK] Revit: {}".format(revit['family_name']))
    
    # Tekla
    tekla = engine.export_to_bim_format(component, "tekla")
    print("[OK] Tekla: {}".format(tekla['model_object']['type']))
    
    # IFC
    ifc = engine.export_to_bim_format(component, "ifc")
    print("[OK] IFC: {}".format(ifc['ifcEntity']))
    
    print("PASS: BIM Export\n")


def test_lod_model():
    print("=== Test: LOD Model ===")
    
    from core.models.lod import (
        Component, LODData, Coordinate3D, ConstructionInfo,
        create_abnormal_column
    )
    
    # Create abnormal column
    column = create_abnormal_column(
        component_id="test-column-001",
        width=0.8,
        height=1.2,
        total_height=3.5,
        slope=0.05
    )
    
    # Add LOD0
    column.add_lod(LODData(
        level=0,
        description="Coarse",
        key_points=[
            Coordinate3D(0, 0, 0),
            Coordinate3D(0, 0, 3.5)
        ]
    ))
    
    # Add LOD1
    column.add_lod(LODData(
        level=1,
        description="Medium",
        boundary_points=[
            Coordinate3D(0, 0, 0),
            Coordinate3D(0.8, 0, 0),
            Coordinate3D(0.8, 1.2, 0),
            Coordinate3D(0, 1.2, 0)
        ]
    ))
    
    # Add construction info
    column.construction_info = ConstructionInfo(
        fabrication_method="CNC切割",
        welding_points=[Coordinate3D(0, 0, 1.0)],
        bolt_holes=[{"diameter": 0.02, "depth": 0.1, "position": {"x": 0, "y": 0, "z": 3.3}}]
    )
    
    # Export JSON
    json_str = column.to_json()
    assert "test-column-001" in json_str
    print("[OK] LOD model JSON: {} chars".format(len(json_str)))
    
    # Verify LOD access
    lod0 = column.get_lod(0)
    assert lod0 is not None
    print("[OK] LOD0 key points: {}".format(len(lod0.key_points)))
    
    print("PASS: LOD Model\n")


def run_all_tests():
    print("\n" + "="*50)
    print("NeuralSite Core - Engineering Module Tests")
    print("="*50 + "\n")
    
    test_lod_model()
    test_construction_recommendation()
    test_collision_detection()
    test_bim_export()
    
    print("="*50)
    print("ALL TESTS PASSED!")
    print("="*50 + "\n")


if __name__ == "__main__":
    run_all_tests()
