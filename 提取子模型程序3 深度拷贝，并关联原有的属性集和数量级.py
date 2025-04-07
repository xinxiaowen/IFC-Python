import datetime
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
import ifcopenshell.util.selector
import sys
import ifcopenshell.util.date

# 输入的IFC文件路径
input_ifc_path = '20201208DigitalHub_ARC.ifc'
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

# # === 新增：明确创建用户历史信息 ===
# schema = original_ifc.schema.upper()

# # 根据版本创建person实体
# if schema in ['IFC4', 'IFC4X3']:
#     person = submodel_ifc.create_entity(
#         "IfcPerson",
#         Identification="Ctesi",
#         FamilyName="WX",
#         GivenName="Default"
#     )
# elif schema in ['IFC2X3', 'IFC2X3TC1']:
#     person = submodel_ifc.create_entity(
#         "IfcPerson",
#         FamilyName="WX",
#         GivenName="Default",
#         MiddleNames=None,
#         PrefixTitles=None,
#         SuffixTitles=None,
#         Roles=None,
#         Addresses=None
#     )
# else:
#     raise Exception(f"不支持的IFC版本: {schema}")

# # 根据版本创建organization实体
# organization = submodel_ifc.create_entity(
#     "IfcOrganization",
#     Name="Ctesi"
# )

# # 创建PersonAndOrganization实例（各版本通用）
# person_and_organization = submodel_ifc.create_entity(
#     "IfcPersonAndOrganization",
#     ThePerson=person,
#     TheOrganization=organization
# )

# # 根据版本创建Application实体
# if schema in ['IFC4', 'IFC4X3']:
#     application = submodel_ifc.create_entity(
#         "IfcApplication",
#         ApplicationDeveloper=organization,
#         Version="1.0",
#         ApplicationFullName="IFC Extractor",
#         ApplicationIdentifier="IFCExtract"
#     )
# elif schema in ['IFC2X3', 'IFC2X3TC1']:
#     application = submodel_ifc.create_entity(
#         "IfcApplication",
#         ApplicationDeveloper=organization,
#         Version="1.0",
#         ApplicationFullName="IFC Extractor",
#         ApplicationIdentifier="IFCExtract"
#     )

# # 最终创建OwnerHistory实体（通用）
# owner_history = submodel_ifc.create_entity(
#     "IfcOwnerHistory",
#     OwningUser=person_and_organization,
#     OwningApplication=application,
#     State=None,
#     ChangeAction="ADDED",
#     LastModifiedDate=None,
#     LastModifyingUser=None,
#     LastModifyingApplication=None,
#     CreationDate=int(datetime.datetime.now().timestamp())
# )

# 创建IFC项目和上下文（通用）
project = ifcopenshell.api.run("root.create_entity", submodel_ifc, ifc_class="IfcProject", name="Extracted Submodel")
# 创建IFC项目和上下文
context = ifcopenshell.api.run("context.add_context", submodel_ifc, context_type="Model")

# 继承原始模型的单位体系
original_units = original_ifc.by_type('IfcUnitAssignment')[0]
submodel_ifc.create_entity('IfcUnitAssignment', Units=original_units.Units)

        
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
                OwnerHistory=project.OwnerHistory,
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
                OwnerHistory=project.OwnerHistory,
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

# 完整复制材质、颜色和贴图
for item in original_ifc.by_type('IfcStyledItem') + original_ifc.by_type('IfcSurfaceStyle'):
    submodel_ifc.add(item)

for relation in original_ifc.by_type('IfcRelAssociatesMaterial'):
    copied_material = ifcopenshell.util.element.copy_deep(submodel_ifc, relation.RelatingMaterial)
    related_objects_copied = [copied_elements[obj.GlobalId] for obj in relation.RelatedObjects if obj.GlobalId in copied_elements]
    if related_objects_copied:
        submodel_ifc.create_entity(
            'IfcRelAssociatesMaterial',
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=project.OwnerHistory,
            RelatedObjects=related_objects_copied,
            RelatingMaterial=copied_material
        )

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

# Select all the walls and slabs in the file.
elements = ifcopenshell.util.selector.filter_elements(original_ifc, "IfcWall, IfcSlab, IfcRoof, IfcStair, IfcRamp, IfcPlate, IfcMember, IfcWindow")
for element in elements:
    # 复制元素并跟踪其属性和数量级
    copied_element = copy_and_track(element)

    # 确保关联到正确的楼层
    original_container = ifcopenshell.util.element.get_container(element)
    if original_container:
        copied_container = copied_storeys[original_storeys.index(original_container)]
        ifcopenshell.api.run(
            "spatial.assign_container",
            submodel_ifc,
            products=[copied_element],
            relating_structure=copied_container
        )

# # 提取所有的IfcWall和IfcDoor构件
# for entity_type in ['IfcWall', 'IfcDoor', 'IfcWindow', 'IfcSlab', 'IfcRoof', 'IfcStair', 'IfcRamp']:
#     elements = original_ifc.by_type(entity_type)
#     for element in elements:
#         copied_element = copy_and_track(element)

#         # 确保关联到正确的楼层
#         original_container = ifcopenshell.util.element.get_container(element)
#         if original_container:
#             copied_container = copied_elements.get(original_container.GlobalId)
#             if copied_container:
#                 ifcopenshell.api.run(
#                     "spatial.assign_container",
#                     submodel_ifc,
#                     products=[copied_element],
#                     relating_structure=copied_container
#                 )

# 完整复制IfcOpeningElement（挖孔）及其关系
for opening_relation in original_ifc.by_type('IfcRelVoidsElement'):
    original_wall = opening_relation.RelatingBuildingElement
    original_opening = opening_relation.RelatedOpeningElement

    if original_wall.GlobalId in copied_elements:
        copied_wall = copied_elements[original_wall.GlobalId]

        # 复制IfcOpeningElement
        copied_opening = ifcopenshell.util.element.copy_deep(submodel_ifc, original_opening)
        copied_elements[original_opening.GlobalId] = copied_opening

        # 建立新的挖孔关系（IfcRelVoidsElement）
        submodel_ifc.create_entity(
            'IfcRelVoidsElement',
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=project.OwnerHistory,
            RelatingBuildingElement=copied_wall,
            RelatedOpeningElement=copied_opening
        )

# 完整复制IfcWindow与OpeningElement之间的填充关系（IfcRelFillsElement）
for fills_relation in original_ifc.by_type('IfcRelFillsElement'):
    original_opening = fills_relation.RelatingOpeningElement
    original_element = fills_relation.RelatedBuildingElement

    if original_opening.GlobalId in copied_elements and original_element.GlobalId in copied_elements:
        copied_opening = copied_elements[original_opening.GlobalId]
        copied_element = copied_elements[original_element.GlobalId]

        # 建立新的填充关系（IfcRelFillsElement）
        submodel_ifc.create_entity(
            'IfcRelFillsElement',
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=project.OwnerHistory,
            RelatingOpeningElement=copied_opening,
            RelatedBuildingElement=copied_element
        )


# 输出元素信息摘要
print("复制元素类型、属性和数量信息：")
for guid, info in element_info.items():
    print(f"GUID: {guid}, 类型: {info['type']}, 属性数量: {info['attributes_count']}")

# 写出子模型IFC文件
submodel_ifc.write(output_ifc_path)
print(f"子模型已成功导出到: {output_ifc_path}")
