import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
import sys

# 输入的IFC文件路径
input_ifc_path = 'SampleHouse.ifc'
# 输出的IFC子模型文件路径
output_ifc_path = 'output_submodel.ifc'

# 打开原始IFC文件
original_ifc = ifcopenshell.open(input_ifc_path)

# 判断IFC文件版本
if original_ifc.schema != 'IFC4':
    print(f"输入文件版本为{original_ifc.schema}，不是IFC4版本！")
    sys.exit(1)

# 创建新的IFC文件
submodel_ifc = ifcopenshell.file(schema='IFC4')
project = ifcopenshell.api.run("root.create_entity", submodel_ifc, ifc_class="IfcProject", name="Extracted Submodel")
context = ifcopenshell.api.run("context.add_context", submodel_ifc, context_type="Model")
ifcopenshell.api.run("unit.assign_unit", submodel_ifc)

# 映射字典
# The `copied_elements` dictionary is used to keep track of the mapping between original elements in
# the original IFC file and their corresponding copied elements in the new submodel IFC file.
# The `copied_elements` dictionary is used to keep track of the mapping between original elements in
# the original IFC file and their corresponding copied elements in the new submodel IFC file.
copied_elements = {}

def copy_and_track(entity):
    copied_entity = ifcopenshell.util.element.copy_deep(submodel_ifc, entity)
    copied_elements[entity.GlobalId] = copied_entity
    return copied_entity

# 复制空间结构（Site, Building, Storey）
original_site = original_ifc.by_type('IfcSite')[0]
original_building = original_ifc.by_type('IfcBuilding')[0]
original_storeys = original_ifc.by_type('IfcBuildingStorey')

copied_site = copy_and_track(original_site)
copied_building = copy_and_track(original_building)
copied_storeys = [copy_and_track(s) for s in original_storeys]

ifcopenshell.api.run("aggregate.assign_object", submodel_ifc, relating_object=project, products=[copied_site])
ifcopenshell.api.run("aggregate.assign_object", submodel_ifc, relating_object=copied_site, products=[copied_building])
ifcopenshell.api.run("aggregate.assign_object", submodel_ifc, relating_object=copied_building, products=copied_storeys)

# 提取所有的IfcWall和IfcDoor构件
for entity_type in ['IfcWall', 'IfcDoor', 'IfcWindow', 'IfcSlab', 'IfcRoof', 'IfcStair', 'IfcRamp']:
    elements = original_ifc.by_type(entity_type)
    for element in elements:
        copied_element = copy_and_track(element)

        # 确保关联到正确的楼层
        original_container = ifcopenshell.util.element.get_container(element)
        if original_container:
            copied_container = copied_elements.get(original_container.GlobalId)
            if copied_container:
                ifcopenshell.api.run(
                    "spatial.assign_container",
                    submodel_ifc,
                    products=[copied_element],
                    relating_structure=copied_container
                )

# 写出子模型IFC文件
submodel_ifc.write(output_ifc_path)
print(f"子模型已成功导出到: {output_ifc_path}")
