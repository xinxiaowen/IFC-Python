import ifcopenshell
import pandas as pd
import win32com.client as win32
xl_app = win32.gencache.EnsureDispatch("Excel.Application")

# Load the IFC file
file_path = "C:/Users/95351/Desktop/IFC File/FXCZ+91-03.00.00.00+70-02.03.03.ifc"  # Replace with your IFC file path
ifc_file = ifcopenshell.open(file_path)

# Function to get all properties of an IFC object
def get_all_properties(ifc_object):
    properties = {
        "GlobalId": ifc_object.GlobalId,
        "Name": ifc_object.Name,
        "ObjectType": ifc_object.ObjectType,
        "Description": ifc_object.Description,
        "PredefinedType": getattr(ifc_object, "PredefinedType", None),
        "Tag":ifc_object.Tag
    }

    # Retrieve property sets
    property_sets = []
    quantities = []

    for definition in ifc_object.IsDefinedBy:
        if definition.is_a("IfcRelDefinesByProperties"):
            # Check if it's a property set
            if definition.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                for prop in definition.RelatingPropertyDefinition.HasProperties:
                    if definition.RelatingPropertyDefinition.Name== 'Construction':    
                        print(definition.RelatingPropertyDefinition.Name)                                                            
                    property_data = {
                        "PropertyName": prop.Name,
                        "PropertyValue": prop.NominalValue.wrappedValue if hasattr(prop, 'NominalValue') else None
                    }
                    properties.update({prop.Name:prop.NominalValue.wrappedValue if hasattr(prop, 'NominalValue') else None})


            # Check if it's a quantity
            elif definition.RelatingPropertyDefinition.is_a("IfcElementQuantity"):
                for quantity in definition.RelatingPropertyDefinition.Quantities:
                    if quantity.is_a("IfcQuantityLength"):
                         q = quantity.LengthValue
                    if quantity.is_a("IfcQuantityVolume"):
                         q = quantity.VolumeValue
                    if quantity.is_a("IfcQuantityArea"):
                         q = quantity.AreaValue
                    if quantity.is_a("IfcQuantityWeight"):
                         q = quantity.WeightValue
                    if quantity.is_a("IfcQuantityCount"):
                         q = quantity.CountValue                         
                    if quantity.is_a("IfcQuantityTime"):
                         q = quantity.TimeValue                               
                    if quantity.is_a("IfcPhysicalComplexQuantity"):
                         for com_p in quantity.HasQuantities:
                            if com_p.is_a("IfcQuantityLength"):
                                q = com_p.LengthValue
                            if com_p.is_a("IfcQuantityVolume"):
                                q = com_p.VolumeValue
                            if com_p.is_a("IfcQuantityArea"):
                                q = com_p.AreaValue
                            if com_p.is_a("IfcQuantityWeight"):
                                 q = com_p.WeightValue                                                            
                            if com_p.is_a("IfcQuantityCount"):
                                q = com_p.CountValue                         
                            if com_p.is_a("IfcQuantityTime"):
                                q = com_p.TimeValue                               
                    properties.update({"数量集：" + quantity.Name:str(q)})
    # properties["PropertySets"] = property_sets
    # properties["Quantities"] = quantities
    return properties

# Function to get type properties of a wall
def get_type_properties(wall):
    type_properties = {}
    
    # Access the wall type through relationships
    for wall_type in wall.IsTypedBy:
        wallType = wall_type.RelatingType
        for prop_set in wallType.HasPropertySets:
                            for prop in prop_set.HasProperties:
                                type_properties.update({"类型属性集：" +prop.Name:prop.NominalValue.wrappedValue if hasattr(prop, 'NominalValue') else None})  
    return type_properties

# # Function to get type properties of a wall
# def get_type_quantities(wall):
#     type_quantities = {}
    
#         # Access the wall type through relationships
#     for wall_type in wall.IsTypedBy:
#         wallType = wall_type.RelatingType
#         for prop_set in wallType.HasPropertySets:
#                             for prop in prop_set.HasProperties:
#                                 type_quantities.update({"类型属性集：" +prop.Name:prop.NominalValue.wrappedValue if hasattr(prop, 'NominalValue') else None})  
#     return type_quantities


# Extract all wall elements (or any specific type)
objects = ifc_file.by_type("IfcBuildingElementProxy")  # Change to the desired IFC object type

# Create a list to store object data with all properties
object_data = []

# Collect object information along with their properties
for obj in objects:
    obj_info = get_all_properties(obj)
    obj_Type_info = get_type_properties(obj)
    obj_info.update(obj_Type_info)
    object_data.append(obj_info)


# Create a DataFrame for object data
df = pd.DataFrame(object_data)

# # Save to Excel
# excel_file_path = "C:/Users/95351/Desktop/IFC File/objects_with_properties.xlsx"  # Specify your Excel file path
# df.to_excel(excel_file_path, index=False)

# xl_app.Visible = True
# # Open the file we want in Excel
# workbook = xl_app.Workbooks.Open(excel_file_path)
import json
with open('C:/Users/95351/Desktop/IFC File/IfcBuildingElementProxy.json', 'w') as f:
    json.dump(object_data, f)

# print(f"Object data with all properties has been successfully exported to {excel_file_path}")
