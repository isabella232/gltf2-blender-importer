from GLTF import *

bl_info = {
    "name": "glTF2 importer",
    "version": (0, 0, 3),
    "author": "Julien Duroure",
    "blender": (2, 79, 0),
    "description": "glTF2 importer",
    "location": "File > Import",
    "category": "Import-Export"
}

#TODO reloading stuff
class ImportglTF2(Operator, ImportHelper):
    bl_idname = 'import_scene.gltf2'
    bl_label  = "Import glTF2"

    loglevel = bpy.props.EnumProperty(items=Log.getLevels(), description="Log Level", default=Log.default())

    def execute(self, context):
        return self.import_gltf2(context)

    def import_gltf2(self, context):
    	# read glTF data
        bpy.context.scene.render.engine = 'CYCLES'
        self.gltf = glTFImporter(self.filepath, self.loglevel)
        self.gltf.log.critical("Starting loading glTF file")
        success, txt = self.gltf.read()
        if not success:
            self.report({'ERROR'}, txt)
            return {'CANCELLED'}

        self.gltf.log.critical("Data are loaded, start creating Blender stuff")
        self.gltf.blender_create()
        self.gltf.debug_missing()
        self.gltf.log.critical("glTF import is now finished")
        self.gltf.log.removeHandler(self.gltf.log_handler)

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportglTF2.bl_idname, text=ImportglTF2.bl_label)

def register():
    bpy.utils.register_class(ImportglTF2)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportglTF2)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()

