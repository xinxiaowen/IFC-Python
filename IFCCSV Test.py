import ifcopenshell
from ifccsv import IfcCsv

model = ifcopenshell.open(r"C:\Users\wenxi\Desktop\20211122Wellness center Sama.ifc")
# Using the selector is optional. You may specify elements as a list manually if you prefer.
# e.g. elements = model.by_type("IfcElement")
elements = ifcopenshell.util.selector.filter_elements(model, "IfcElement")
attributes = ["Tag","class","Name", "Description","ObjectType","Pset_ProductRequirements.Category","Pset_ElementShading.Roughness"]

# Export our model's elements and their attributes to a CSV.
ifc_csv = IfcCsv()
ifc_csv.export(model, elements, attributes, output="out.csv", format="csv", delimiter=",", null="-")

# Optionally, you can explicitly export to different formats.
# ifc_csv = IfcCsv()
# ifc_csv.export(model, elements, attributes)
ifc_csv.export_csv("out.csv", delimiter=";")
ifc_csv.export_xlsx("out.xlsx") 

# Optionally, you can create a Pandas DataFrame.
df = ifc_csv.export_pd()
print(df)

# # Optionally, you can directly fetch the headers and rows as Python lists.
# print(ifc_csv.headers)
# print(ifc_csv.results)

# # You can also import changes from a CSV
# ifc_csv.Import(model, "input.csv")
# model.write("/path/to/updated_model.ifc")
