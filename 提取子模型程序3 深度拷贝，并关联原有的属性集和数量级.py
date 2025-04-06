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

# 支持的IFC文件版本列表
supported_versions = ['IFC4', 'IFC4X3', 'IFC2X3', 'IFC2X3TC1']

# 判断IFC文件版本
if original_ifc.schema.upper() not in supported_versions:
    print(f"输入文件版本为{original_ifc.schema}，不在支持的版本列表中：{', '.join(supported_versions)}")
    sys.exit(1)

# 创建新的IFC文件
submodel_ifc = ifcopenshell.file(schema=original_ifc.schema)
project = ifcopenshell.api.run("root.create_entity", submodel_ifc, ifc_class="IfcProject", name="Extracted Submodel")
# 创建IFC项目和上下文
context = ifcopenshell.api.run("context.add_context", submodel_ifc, context_type="Model")
ifcopenshell.api.run("unit.assign_unit", submodel_ifc)

# 映射字典
copied_elements = {}
element_info = {}

def copy_and_track(entity):
    copied_entity = ifcopenshell.util.element.copy_deep(submodel_ifc, entity)
    copied_elements[entity.GlobalId] = copied_entity

    # 使用 get_info() 获取属性信息
    entity_info = entity.get_info()
    entity_type = entity_info['type']
    properties = entity_info  # 完整属性字典
    element_info[entity.GlobalId] = {
        'type': entity_type,
        'properties': properties,
        'attributes_count': len(properties) - 1  # 减去'type'字段本身
    }
    
    # 复制关联的PropertySet和QuantitySet
    for definition in original_ifc.by_type('IfcRelDefinesByProperties'):
        if entity in definition.RelatedObjects:
            copied_pset = ifcopenshell.util.element.copy_deep(submodel_ifc, definition.RelatingPropertyDefinition)
            # 创建IfcRelDefinesByProperties关系并关联到实体
            submodel_ifc.create_entity(
                'IfcRelDefinesByProperties',
                GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=definition.OwnerHistory,
                Name=definition.Name,
                Description=definition.Description,
                RelatedObjects=[copied_entity],
                RelatingPropertyDefinition=copied_pset
            )
            
        # 补充复制关联的IfcTypeObject类型定义
    for definition in original_ifc.by_type('IfcRelDefinesByType'):
        if entity in definition.RelatedObjects:
            copied_type_object = ifcopenshell.util.element.copy_deep(
                submodel_ifc, definition.RelatingType
            )
            submodel_ifc.create_entity(
                'IfcRelDefinesByType',
                GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=definition.OwnerHistory,
                Name=definition.Name,
                Description=definition.Description,
                RelatedObjects=[copied_entity],
                RelatingType=copied_type_object
            )
                    
    # # === 新增：创建并关联bSDD引用属性 ===
    # # 假设已知bSDD属性的URI（例如："https://identifier.buildingsmart.org/uri/...属性定义的URI..."）
    # bSDD_property_uri = "https://identifier.buildingsmart.org/uri/sample-bSDD-property"

    # # 创建 bSDD 属性引用
    # bSDD_property = submodel_ifc.create_entity(
    #     "IfcPropertyReferenceValue",
    #     Name="bSDDProperty",
    #     Description="关联到bSDD标准属性",
    #     UsageName=None,
    #     PropertyReference=submodel_ifc.create_entity(
    #         "IfcExternalReference",
    #         Location=bSDD_property_uri,
    #         Identification=None,
    #         Name="bSDD Reference"
    #     )
    # )

    # # 创建属性集（PropertySet），并包含 bSDD 属性引用
    # bSDD_pset = submodel_ifc.create_entity(
    #     "IfcPropertySet",
    #     GlobalId=ifcopenshell.guid.new(),
    #     OwnerHistory=None,
    #     Name="Pset_bSDD",
    #     Description="包含bSDD关联属性",
    #     HasProperties=[bSDD_property]
    # )

    # # 通过 IfcRelDefinesByProperties 关联到元素上
    # submodel_ifc.create_entity(
    #     "IfcRelDefinesByProperties",
    #     GlobalId=ifcopenshell.guid.new(),
    #     OwnerHistory=None,
    #     Name="bSDD属性关联",
    #     Description="将bSDD标准属性关联到元素上",
    #     RelatedObjects=[copied_entity],
    #     RelatingPropertyDefinition=bSDD_pset
    # )

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

# 输出元素信息摘要
print("复制元素类型、属性和数量信息：")
for guid, info in element_info.items():
    print(f"GUID: {guid}, 类型: {info['type']}, 属性数量: {info['attributes_count']}")

# 写出子模型IFC文件
submodel_ifc.write(output_ifc_path)
print(f"子模型已成功导出到: {output_ifc_path}")
