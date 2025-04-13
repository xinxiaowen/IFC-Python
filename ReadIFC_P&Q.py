import ifcopenshell
import csv
import json

# 打开 IFC 文件
ifc_file = ifcopenshell.open(
    "2022020320211122Wellness center Sama.ifc")  # 替换为你的 IFC 文件路径

# 目标构件类型
target_types = ["IfcWall", "IfcDoor", "IfcWindow", "IfcSlab",
                "IfcBeam", "IfcColumn", "IfcStair", "IfcRailing",
                "IfcRoof", "IfcBuildingElementProxy"]

# 收集所有目标构件
elements = [
    elem for type_name in target_types for elem in ifc_file.by_type(type_name)]

# CSV 文件路径
csv_file = "./Ifc_toCSV/ifc_complete_export.csv"

# 打开 CSV 文件写入
with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    # 写入表头
    writer.writerow([
        "ElementType",
        "GlobalId",
        "Name",
        "ObjectType",
        "PredefinedType",
        "Tag",
        "Description",
        "TypeName",  # 类型名称
        "DataSource",  # 来源：BaseProperty / PropertySet / QuantitySet / TypePropertySet
        "SetName",
        "PropertyName",
        "PropertyValue"
    ])

    # 遍历构件
    for elem in elements:
        element_type = elem.is_a()
        global_id = elem.GlobalId
        name = elem.Name if elem.Name else ""
        object_type = elem.ObjectType if hasattr(
            elem, "ObjectType") and elem.ObjectType else ""
        predefined_type = elem.PredefinedType if hasattr(
            elem, "PredefinedType") and elem.PredefinedType else ""
        tag = elem.Tag if hasattr(elem, "Tag") and elem.Tag else ""
        description = elem.Description if hasattr(
            elem, "Description") and elem.Description else ""

        # 获取类型定义
        type_name = ""
        type_object = None
        if hasattr(elem, "IsDefinedBy"):
            for rel in elem.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByType"):
                    type_object = rel.RelatingType
                    if type_object:
                        type_name = type_object.Name if type_object.Name else ""

        # --- 2. 写入属性集 ---
        if hasattr(elem, "IsDefinedBy"):
            for rel in elem.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    definition = rel.RelatingPropertyDefinition

                    if definition.is_a("IfcPropertySet"):
                        set_name = definition.Name

                        for prop in definition.HasProperties:
                            prop_name = prop.Name
                            prop_value = prop.NominalValue.wrappedValue if hasattr(
                                prop, "NominalValue") and prop.NominalValue else ""

                            writer.writerow([
                                element_type,
                                global_id,
                                name,
                                object_type,
                                predefined_type,
                                tag,
                                description,
                                type_name,
                                "PropertySet",
                                set_name,
                                prop_name,
                                prop_value
                            ])

        # --- 3. 写入数量集 ---
        if hasattr(elem, "IsDefinedBy"):
            for rel in elem.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    definition = rel.RelatingPropertyDefinition

                    if definition.is_a("IfcElementQuantity"):
                        set_name = definition.Name

                        for quantity in definition.Quantities:
                            quantity_name = quantity.Name

                            # 判断数量类型获取对应值
                            if quantity.is_a("IfcQuantityLength"):
                                quantity_value = quantity.LengthValue
                            elif quantity.is_a("IfcQuantityArea"):
                                quantity_value = quantity.AreaValue
                            elif quantity.is_a("IfcQuantityVolume"):
                                quantity_value = quantity.VolumeValue
                            elif quantity.is_a("IfcQuantityCount"):
                                quantity_value = quantity.CountValue
                            elif quantity.is_a("IfcQuantityWeight"):
                                quantity_value = quantity.WeightValue
                            else:
                                quantity_value = "Unsupported quantity type"

                            writer.writerow([
                                element_type,
                                global_id,
                                name,
                                object_type,
                                predefined_type,
                                tag,
                                description,
                                type_name,
                                "QuantitySet",
                                set_name,
                                quantity_name,
                                quantity_value
                            ])

        # --- 4. 写入关联的类型属性集 ---
        # if type_object:
        #     if hasattr(type_object, "HasPropertySets"):
        #         for pset in type_object.HasPropertySets:
        #             set_name = pset.Name
        #             if hasattr(pset, "HasProperties"):
        #                 for prop in pset.HasProperties:
        #                     prop_name = prop.Name
        #                     prop_value = prop.NominalValue.wrappedValue if hasattr(
        #                         prop, "NominalValue") and prop.NominalValue else ""

        #                     writer.writerow([
        #                         element_type,
        #                         global_id,
        #                         name,
        #                         object_type,
        #                         predefined_type,
        #                         tag,
        #                         description,
        #                         type_name,
        #                         "TypePropertySet",
        #                         set_name,
        #                         prop_name,
        #                         prop_value
        #                     ])

print(f"构件基础属性 + 构件属性集 + 数量集 + 类型属性集 已成功导出到 {csv_file}")

# 目标 JSON 文件路径
json_file = "./Ifc_toCSV/ifc_properties_quantities.json"

# 读取 CSV 并写入 JSON
with open(csv_file, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

with open(json_file, mode='w', encoding='utf-8') as f:
    json.dump(rows, f, indent=4, ensure_ascii=False)

print(f"CSV 文件已成功导出为 JSON：{json_file}")
