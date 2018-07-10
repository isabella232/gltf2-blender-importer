import bpy
from .pbr import *
from .emissivemap import *
from .normalmap import *
from .occlusionmap import *

def blender_material(current):
    if current.name is not None:
        name = current.name
    else:
        name = "Material_" + str(current.index)

    mat = bpy.data.materials.new(name)
    current.blender_material = mat.name

    # create pbr material
    blender_pbr(current.pbr, mat.name)

    if current.alphaMode != 'OPAQUE':
        blender_alpha(current, mat.name)

    # add emission map if needed
    if current.emissivemap:
        blender_emissive(current.emissivemap, mat.name)

    # add normal map if needed
    if current.normalmap:
        blender_normalmap(current.normalmap, mat.name)

    # add occlusion map if needed
    # will be pack, but not used
    if current.occlusionmap:
        blender_occlusion(current.occlusionmap, mat.name)

    # if current.doubleSided == False:
    #     blender_single_sided(current, mat.name)

def set_uvmap(current, prim, obj):
    node_tree = bpy.data.materials[current.blender_material].node_tree
    uvmap_nodes =  [node for node in node_tree.nodes if node.type == 'UVMAP']
    for uvmap_node in uvmap_nodes:
        if uvmap_node["gltf2_texcoord"] in prim.blender_texcoord.keys():
            uvmap_node.uv_map = prim.blender_texcoord[uvmap_node["gltf2_texcoord"]]