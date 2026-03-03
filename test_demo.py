# Test
import sys
sys.path.insert(0, '.')

from core import NeuralSiteEngine
from agents.parser import DesignParser
from output.model.generator import ModelGenerator, EarthworkCalculator

print("=== NeuralSite Core Demo ===\n")

# 1. Parse
print("1. Parse...")
parser = DesignParser()
text = "主线: R=800, LS=120, K0+000"
result = parser.parse_text(text)
print(f"   Input: {text}")
print(f"   Elements: {len(result.get('horizontal', []))}")

# 2. Calculate
print("\n2. Calculate...")
engine = NeuralSiteEngine("DEMO")
engine.load_from_json(parser.to_engine_format())
coord = engine.get_coordinate(500)
print(f"   K0+500: X={coord.x:.2f} Y={coord.y:.2f} Z={coord.z:.2f}")

# 3. Cross section
print("\n3. Cross Section...")
cs = engine.calculate_cross_section(500)
print(f"   Center: ({cs['center'][0]:.2f}, {cs['center'][1]:.2f}, {cs['center'][2]:.2f})")

# 4. Model
print("\n4. Generate 3D Model...")
coords = engine.calculate_range(0, 500, 100)
gen = ModelGenerator()
gen.generate_mesh(coords, width=10)
print(f"   Vertices: {len(gen.vertices)}")
print(f"   Faces: {len(gen.faces)}")

# 5. Earthwork
print("\n5. Earthwork Calculation...")
calc = EarthworkCalculator()
calc.add_section(0, 100)
calc.add_section(500, 120)
volume = calc.calculate_volume()
print(f"   Fill: {volume['fill']:.0f} m3")
print(f"   Cut: {volume['cut']:.0f} m3")

print("\n=== Complete ===")
