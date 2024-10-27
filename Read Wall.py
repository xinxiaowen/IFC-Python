# Importing necessary libraries
import ifcopenshell
import ifcopenshell.util.element
import pandas as pd

# Load the IFC file
file_path = "C:/Users/95351/Desktop/IFC File/SampleHouse.ifc"  # replace with your IFC file path
ifc_file = ifcopenshell.open(file_path)

# Extract all wall elements
walls = ifc_file.by_type("IfcWall")

# Function to get openings associated with a wall
def get_openings(wall):
    openings = []
    for rel in wall.HasOpenings:
        if rel.is_a("IfcRelVoidsElement"):
            opening = rel.RelatedOpeningElement
            openings.append({
                "GlobalId": opening.GlobalId,
                "Name": opening.Name,
                "ObjectType": opening.ObjectType,
                "PredefinedType": getattr(opening, "PredefinedType", None),
                "Description": opening.Description,
                # Additional attributes can be added here if needed
            })
            print(opening)
    return openings

def get_all_properties(ifc_object):
    properties = {
        "GlobalId": ifc_object.GlobalId,
        "Name": ifc_object.Name,
        "ObjectType": ifc_object.ObjectType,
        "Description": ifc_object.Description,
        "PredefinedType": getattr(ifc_object, "PredefinedType", None),
    }

# Create a list to store wall data with openings
wall_data = []

# Collect wall information along with their openings
for wall in walls:
    wall_info = {
        "GlobalId": wall.GlobalId,
        "Name": wall.Name,
        "ObjectType": wall.ObjectType,
        "PredefinedType": getattr(wall, "PredefinedType", None),
        "Description": wall.Description,
        "Openings": get_openings(wall),  # Get the openings for this wall
    }
    wall_data.append(wall_info)

# Expand openings into separate rows
expanded_data = []
for wall in wall_data:
    for opening in wall["Openings"]:
        expanded_data.append({**wall, **opening})

# Create a DataFrame from expanded data
expanded_df = pd.DataFrame(expanded_data)

# Save to Excel
#excel_file_path = "C:/Users/95351/Desktop/IFC File/walls_with_openings.xlsx"  # Specify your Excel file path
#expanded_df.to_excel(excel_file_path, index=False)
