from ifcpatch import extract_docs
import ifctester
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.selector
import ifcopenshell.util.placement
import ifcpatch

model = ifcopenshell.open("SampleHouse.ifc")

# Extract all walls and slabs
output = ifcpatch.execute({"input": "SampleHouse.ifc", "file": model, "recipe": "SplitByBuildingStorey", "arguments": [
                          r"G:\2025年工作文件夹\16 博士课程及论文\论文资料准备\IFC Split"]})
print("Extracted walls and slabs to output.ifc")

# Extract all walls and slabs
output = ifcpatch.execute({"input": "input.ifc", "file": model,
                          "recipe": "ExtractElements", "arguments": ["IfcWall, IfcSlab"]})
ifcpatch.write(output, "output.ifc")
print("Extracted walls and slabs to output.ifc")

# Extract all walls and slabs with a specific property set
result = ifcpatch.execute(
    {"input": "input.ifc", "file": model, "recipe": "ExtractPropertiesToSQLite"})
ifcpatch.write(result, "output1.sqlite")
print("Extracted properties to output1.sqlite")

# Convert to SQLite, SQLite databse will be saved to a temporary file.
result = sqlite_temp_filepath = ifcpatch.execute(
    {"input": "input.ifc", "file": model,
        "recipe": "Ifc2Sql", "arguments": ["sqlite"], "full_schema": False, "is_strict": False, "should_get_psets": True, "should_expand": False, "should_get_geometry": True, "should_skip_geometry_data": False})
ifcpatch.write(result, "output2.sqlite")
print("Converted to SQLite and saved to output2.sqlite")
