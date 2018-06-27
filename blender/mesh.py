"""
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor(s): Julien Duroure.
 *
 * ***** END GPL LICENSE BLOCK *****
 * This development is done in strong collaboration with Airbus Defence & Space
 """

import bpy
import bmesh
from mathutils import Vector
from .utils import Conversion
from .material import *

def blender_mesh(gltf_mesh, parent):
    # Check if the mesh is rigged, and create armature if needed
    if gltf_mesh.skin:
        if gltf_mesh.skin.blender_armature_name is None:
            # Create empty armature for now
            gltf_mesh.skin.create_blender_armature(parent)

    # Geometry
    if gltf_mesh.name:
        mesh_name = gltf_mesh.name
    else:
        mesh_name = "Mesh_" + str(gltf_mesh.index)

    mesh = bpy.data.meshes.new(mesh_name)
    verts = []
    edges = []
    faces = []
    for prim in gltf_mesh.primitives:
        verts, edges, faces = blender_primitive(prim, verts, edges, faces)

    mesh.from_pydata(verts, edges, faces)
    mesh.validate()

    return mesh

def blender_set_mesh(gltf_mesh, mesh, obj):
    # Normals
    offset = 0
    for prim in gltf_mesh.primitives:
        offset = blender_set_normals(prim, mesh, offset)

    mesh.update()

    # manage UV
    offset = 0
    for prim in gltf_mesh.primitives:
        offset = blender_set_UV(prim, obj, mesh, offset)

    mesh.update()

    # Object and UV are now created, we can set UVMap into material
    for prim in gltf_mesh.primitives:
        blender_set_UV_in_mat(prim, obj)

    # Assign materials to mesh
    offset = 0
    cpt_index_mat = 0
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for prim in gltf_mesh.primitives:
        offset, cpt_index_mat = blender_assign_material(prim, obj, bm, offset, cpt_index_mat)

    bm.to_mesh(obj.data)
    bm.free()

    # Create shapekeys if needed
    max_shape_to_create = 0
    for prim in gltf_mesh.primitives:
        if len(prim.targets) > max_shape_to_create:
            max_shape_to_create = len(prim.targets)

    # Create basis shape key
    if max_shape_to_create > 0:
        obj.shape_key_add("Basis")

    for i in range(max_shape_to_create):

        obj.shape_key_add("target_" + str(i))

        for prim in gltf_mesh.primitives:
            if i > len(prim.targets):
                continue

            bm = bmesh.new()
            bm.from_mesh(mesh)

            shape_layer = bm.verts.layers.shape[i+1]
            vert_idx = 0
            for vert in bm.verts:
                shape = vert[shape_layer]
                co = Conversion.location(list(prim.targets[i]['POSITION']['result'][vert_idx]))
                shape.x = obj.data.vertices[vert_idx].co.x + co[0]
                shape.y = obj.data.vertices[vert_idx].co.y + co[1]
                shape.z = obj.data.vertices[vert_idx].co.z + co[2]

                vert_idx += 1

            bm.to_mesh(obj.data)
            bm.free()

    # set default weights for shape keys, and names
    for i in range(max_shape_to_create):
        if i < len(gltf_mesh.target_weights):
            obj.data.shape_keys.key_blocks[i+1].value = gltf_mesh.target_weights[i]
            if gltf_mesh.primitives[0].targets[i]['POSITION']['accessor'].name:
               obj.data.shape_keys.key_blocks[i+1].name  = gltf_mesh.primitives[0].targets[i]['POSITION']['accessor'].name


    # Apply vertex color.
    vertex_color = None
    offset = 0
    for prim in gltf_mesh.primitives:
        if 'COLOR_0' in prim.attributes.keys():
            # Create vertex color, once only per object
            if vertex_color is None:
                vertex_color = obj.data.vertex_colors.new("COLOR_0")

            color_data = prim.attributes['COLOR_0']['result']

            for poly in mesh.polygons:
                for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    vert_idx = mesh.loops[loop_idx].vertex_index
                    if vert_idx in range(offset, offset + prim.vertices_length):
                        if offset != 0:
                            cpt_idx = vert_idx % offset
                        else:
                            cpt_idx = vert_idx
                        vertex_color.data[loop_idx].color = color_data[cpt_idx][0:3]
                        #TODO : no alpha in vertex color
        offset = offset + prim.vertices_length

def blender_primitive(gltf_primitive, verts, edges, faces):
    # TODO mode of primitive 4 for now.
    current_length = len(verts)
    prim_verts = [Conversion.location(vert) for vert in gltf_primitive.attributes['POSITION']['result']]
    gltf_primitive.vertices_length = len(prim_verts)
    verts.extend(prim_verts)
    prim_faces = []
    for i in range(0, len(gltf_primitive.indices), 3):
        vals = gltf_primitive.indices[i:i+3]
        new_vals = []
        for y in vals:
            new_vals.append(y+current_length)
        prim_faces.append(tuple(new_vals))
    faces.extend(prim_faces)
    gltf_primitive.faces_length = len(prim_faces)

    # manage material of primitive
    if gltf_primitive.mat:

        # Create Blender material
        if not gltf_primitive.mat.blender_material:
            blender_material(gltf_primitive.mat)

    return verts, edges, faces


def blender_set_normals(gltf_primitive, mesh, offset):
    if 'NORMAL' in gltf_primitive.attributes.keys():
        for poly in mesh.polygons:
            for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                vert_idx = mesh.loops[loop_idx].vertex_index
                if vert_idx in range(offset, offset + gltf_primitive.vertices_length):
                    if offset != 0:
                        cpt_vert = vert_idx % offset
                    else:
                        cpt_vert = vert_idx
                    mesh.vertices[vert_idx].normal = gltf_primitive.attributes['NORMAL']['result'][cpt_vert]
    offset = offset + gltf_primitive.vertices_length
    return offset

def blender_set_UV(gltf_primitive, obj, mesh, offset):
    for texcoord in [attr for attr in gltf_primitive.attributes.keys() if attr[:9] == "TEXCOORD_"]:
        if not texcoord in mesh.uv_textures:
            mesh.uv_textures.new(texcoord)
            gltf_primitive.blender_texcoord[int(texcoord[9:])] = texcoord

        for poly in mesh.polygons:
            for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                vert_idx = mesh.loops[loop_idx].vertex_index
                if vert_idx in range(offset, offset + gltf_primitive.vertices_length):
                    obj.data.uv_layers[texcoord].data[loop_idx].uv = Vector((gltf_primitive.attributes[texcoord]['result'][vert_idx-offset][0], 1-gltf_primitive.attributes[texcoord]['result'][vert_idx-offset][1]))

    offset = offset + gltf_primitive.vertices_length
    return offset


def blender_set_UV_in_mat(gltf_primitive, obj):
    if hasattr(gltf_primitive.mat, "KHR_materials_pbrSpecularGlossiness"):
        if gltf_primitive.mat.KHR_materials_pbrSpecularGlossiness.diffuse_type in [gltf_primitive.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE, gltf_primitive.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE_FACTOR]:
            set_uvmap(gltf_primitive.mat, gltf_primitive, obj)
        else:
            if gltf_primitive.mat.KHR_materials_pbrSpecularGlossiness.specgloss_type in [gltf_primitive.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE, gltf_primitive.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE_FACTOR]:
                set_uvmap(gltf_primitive.mat, gltf_primitive, obj)

    else:
        if gltf_primitive.mat.pbr.color_type in [gltf_primitive.mat.pbr.TEXTURE, gltf_primitive.mat.pbr.TEXTURE_FACTOR] :
            set_uvmap(gltf_primitive.mat, gltf_primitive, obj)
        else:
            if gltf_primitive.mat.pbr.metallic_type in [gltf_primitive.mat.pbr.TEXTURE, gltf_primitive.mat.pbr.TEXTURE_FACTOR] :
                set_uvmap(gltf_primitive.mat, gltf_primitive, obj)


def blender_assign_material(gltf_primitive, obj, bm, offset, cpt_index_mat):
    obj.data.materials.append(bpy.data.materials[gltf_primitive.mat.blender_material])
    for vert in bm.verts:
        if vert.index in range(offset, offset + gltf_primitive.vertices_length):
            for loop in vert.link_loops:
                face = loop.face.index
                bm.faces[face].material_index = cpt_index_mat
    cpt_index_mat += 1
    offset = offset + gltf_primitive.vertices_length
    return offset, cpt_index_mat