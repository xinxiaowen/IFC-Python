import ifcopenshell
from ifccsv import IfcCsv
import json
import csv

model = ifcopenshell.open("SampleHouse.ifc")
# Using the selector is optional. You may specify elements as a list manually if you prefer.
# e.g. elements = model.by_type("IfcElement")
elements = ifcopenshell.util.selector.filter_elements(model, "IfcElement")
attributes = ["Tag", "class", "Name", "Description",
              "ObjectType", "Pset_ProductRequirements.Category", "Pset_ElementShading.Roughness"]

# Export our model's elements and their attributes to a CSV.
ifc_csv = IfcCsv()
ifc_csv.export(model, elements, attributes, output="./Ifc_toCSV/out.csv",
               format="csv", delimiter=",", null="-")

# Optionally, you can explicitly export to different formats.
# ifc_csv = IfcCsv()
# ifc_csv.export(model, elements, attributes)
# ifc_csv.export_csv("./Ifc_toCSV/out.csv", delimiter=";")
ifc_csv.export_ods("./Ifc_toCSV/out.ods")
ifc_csv.export_xlsx("./Ifc_toCSV/out.xlsx")

# Optionally, you can create a Pandas DataFrame.
df = ifc_csv.export_pd()
print(df)

df.to_json("./Ifc_toCSV/out.json", orient="records",
           force_ascii=False, indent=4)

# # 目标 JSON 文件路径
# json_file = "./Ifc_toCSV/out.json"

# # 读取 CSV 并写入 JSON
# with open("./Ifc_toCSV/out.csv", mode='r', encoding='utf-8') as f:
#     reader = csv.DictReader(f)
#     rows = list(reader)

# with open(json_file, mode='w', encoding='utf-8') as f:
#     json.dump(rows, f, indent=4, ensure_ascii=False)

# print(f"CSV 文件已成功导出为 JSON：{json_file}")


# Optionally, you can directly fetch the headers and rows as Python lists.
print(ifc_csv.headers)
print(ifc_csv.results)

# You can also import changes from a CSV
# ifc_csv.Import(model, "input.csv")
# model.write("/path/to/updated_model.ifc")
