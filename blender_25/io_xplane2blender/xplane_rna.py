import bpy

def add_xplane_rna(obj):
    obj["xplane"] = {
        "use":False,
        "export":False,
        "exportFile":'',
        "dataref":''
        }