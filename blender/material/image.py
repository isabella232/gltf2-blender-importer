import bpy
import tempfile
import os

def blender_image(current):
    # Create a temp image, pack, and delete image
    tmp_image = tempfile.NamedTemporaryFile(delete=False)
    tmp_image.write(current.data)
    tmp_image.close()

    blender_image = bpy.data.images.load(tmp_image.name)
    blender_image.pack()
    blender_image.name = "Image_" + str(current.index)
    current.blender_image_name = blender_image.name
    os.remove(tmp_image.name)