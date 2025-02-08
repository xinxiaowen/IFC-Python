import pprint
import ifcopenshell
import ifcopenshell.util.element as Element
import json

file = ifcopenshell.open(
    r"C:\Users\wenxi\Desktop\20211122Wellness center Sama.ifc")


def get_objects_data_by_class(file, class_type):
    objects_data = []
    objects = file.by_type(class_type)
    for object in objects:
        object_id = object.id()
        objects_data.append({
            "ExpressID": object.id(),
            "GlobalId": object.GlobalId,
            "Class": object.is_a(),
            "PredefinedType": Element.get_predefined_type(object),
            "Name": object.Name,
            "Level": Element.get_container(object).Name
            if Element.get_container(object)
            else "",
            "ObjectType": Element.get_type(object).Name
            if Element.get_type(object)
            else "",
            "QuantitySets": Element.get_psets(object, qtos_only=True),
            "PropertySets": Element.get_psets(object, psets_only=True),
        })
    return objects_data

data = get_objects_data_by_class(file, "IfcElement")

json_file_path = './models/result.json'
json_file = open(json_file_path, mode='w')
json.dump(data,json_file,indent=4)

# pp = pprint.PrettyPrinter()
# data = pp.pprint(get_objects_data_by_class(file, "IfcBuildingElement"))
# print(data)
