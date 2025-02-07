import ifcpatch
import ifcopenshell


def ExtractPropertiesToSQLite():
    inputfile = r"C:\Users\wenxi\Desktop\20211122Wellness center Sama.ifc"
    outputfile = r"C:\Users\wenxi\Desktop\20211122Wellness center Sama.sqlite"
    output = ifcpatch.execute({
        "input": inputfile,
        "file": ifcopenshell.open(inputfile),
        "recipe": "ExtractPropertiesToSQLite",
    })
    ifcpatch.write(output, outputfile)
    print("将IFC文件导出为sqllite文件成功！")


ExtractPropertiesToSQLite()
