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

def blender_mesh(current):
        # Check if the mesh is rigged, and create armature if needed
        if self.skin:
            if self.skin.blender_armature_name is None:
                # Create empty armature for now
                self.skin.create_blender_armature(parent)

        # Geometry
        if self.name:
            mesh_name = self.name
        else:
            mesh_name = "Mesh_" + str(self.index)

        mesh = bpy.data.meshes.new(mesh_name)
        verts = []
        edges = []
        faces = []
        for prim in self.primitives:
            verts, edges, faces = prim.blender_create(verts, edges, faces)

        mesh.from_pydata(verts, edges, faces)
        mesh.validate()

        return mesh

def blender_set_mesh(self, mesh, obj):

        # Normals
        offset = 0
        for prim in self.primitives:
            offset = prim.blender_set_normals(mesh, offset)

        mesh.update()

        # manage UV
        offset = 0
        for prim in self.primitives:
            offset = prim.blender_set_UV(obj, mesh, offset)

        mesh.update()

        # Object and UV are now created, we can set UVMap into material
        for prim in self.primitives:
            prim.blender_set_UV_in_mat(obj)

        # Assign materials to mesh
        offset = 0
        cpt_index_mat = 0
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for prim in self.primitives:
            offset, cpt_index_mat = prim.blender_assign_material(obj, bm, offset, cpt_index_mat)

        bm.to_mesh(obj.data)
        bm.free()

        # Create shapekeys if needed
        max_shape_to_create = 0
        for prim in self.primitives:
            if len(prim.targets) > max_shape_to_create:
                max_shape_to_create = len(prim.targets)

        # Create basis shape key
        if max_shape_to_create > 0:
            obj.shape_key_add("Basis")

        for i in range(max_shape_to_create):

            obj.shape_key_add("target_" + str(i))

            for prim in self.primitives:
                if i > len(prim.targets):
                    continue

                bm = bmesh.new()
                bm.from_mesh(mesh)

                shape_layer = bm.verts.layers.shape[i+1]
                vert_idx = 0
                for vert in bm.verts:
                    shape = vert[shape_layer]
                    co = self.gltf.convert.location(list(prim.targets[i]['POSITION']['result'][vert_idx]))
                    shape.x = obj.data.vertices[vert_idx].co.x + co[0]
                    shape.y = obj.data.vertices[vert_idx].co.y + co[1]
                    shape.z = obj.data.vertices[vert_idx].co.z + co[2]

                    vert_idx += 1

                bm.to_mesh(obj.data)
                bm.free()

        # set default weights for shape keys, and names
        for i in range(max_shape_to_create):
            if i < len(self.target_weights):
                obj.data.shape_keys.key_blocks[i+1].value = self.target_weights[i]
                if self.primitives[0].targets[i]['POSITION']['accessor'].name:
                   obj.data.shape_keys.key_blocks[i+1].name  = self.primitives[0].targets[i]['POSITION']['accessor'].name


        # Apply vertex color.
        vertex_color = None
        offset = 0
        for prim in self.primitives:
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

def blender_primitive(current, verts, edges, faces):
    # TODO mode of primitive 4 for now.
    current_length = len(verts)
    prim_verts = [self.gltf.convert.location(vert) for vert in self.attributes['POSITION']['result']]
    self.vertices_length = len(prim_verts)
    verts.extend(prim_verts)
    prim_faces = []
    for i in range(0, len(self.indices), 3):
        vals = self.indices[i:i+3]
        new_vals = []
        for y in vals:
            new_vals.append(y+current_length)
        prim_faces.append(tuple(new_vals))
    faces.extend(prim_faces)
    self.faces_length = len(prim_faces)

    # manage material of primitive
    if self.mat:

        # Create Blender material
        if not self.mat.blender_material:
            self.mat.create_blender()

    return verts, edges, faces


def blender_set_normals(current, mesh, offset):
    if 'NORMAL' in self.attributes.keys():
        for poly in mesh.polygons:
            for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                vert_idx = mesh.loops[loop_idx].vertex_index
                if vert_idx in range(offset, offset + self.vertices_length):
                    if offset != 0:
                        cpt_vert = vert_idx % offset
                    else:
                        cpt_vert = vert_idx
                    mesh.vertices[vert_idx].normal = self.attributes['NORMAL']['result'][cpt_vert]
    offset = offset + self.vertices_length
    return offset

def blender_set_UV(current, obj, mesh, offset):
    for texcoord in [attr for attr in self.attributes.keys() if attr[:9] == "TEXCOORD_"]:
        if not texcoord in mesh.uv_textures:
            mesh.uv_textures.new(texcoord)
            self.blender_texcoord[int(texcoord[9:])] = texcoord

        for poly in mesh.polygons:
            for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                vert_idx = mesh.loops[loop_idx].vertex_index
                if vert_idx in range(offset, offset + self.vertices_length):
                    obj.data.uv_layers[texcoord].data[loop_idx].uv = Vector((self.attributes[texcoord]['result'][vert_idx-offset][0], 1-self.attributes[texcoord]['result'][vert_idx-offset][1]))

    offset = offset + self.vertices_length
    return offset


def blender_set_UV_in_mat(current, obj):
    if hasattr(self.mat, "KHR_materials_pbrSpecularGlossiness"):
        if self.mat.KHR_materials_pbrSpecularGlossiness.diffuse_type in [self.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE, self.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE_FACTOR]:
            self.mat.set_uvmap(self, obj)
        else:
            if self.mat.KHR_materials_pbrSpecularGlossiness.specgloss_type in [self.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE, self.mat.KHR_materials_pbrSpecularGlossiness.TEXTURE_FACTOR]:
                self.mat.set_uvmap(self, obj)

    else:
        if self.mat.pbr.color_type in [self.mat.pbr.TEXTURE, self.mat.pbr.TEXTURE_FACTOR] :
            self.mat.set_uvmap(self, obj)
        else:
            if self.mat.pbr.metallic_type in [self.mat.pbr.TEXTURE, self.mat.pbr.TEXTURE_FACTOR] :
                self.mat.set_uvmap(self, obj)


def blender_assign_material(current, obj, bm, offset, cpt_index_mat):
    obj.data.materials.append(bpy.data.materials[self.mat.blender_material])
    for vert in bm.verts:
        if vert.index in range(offset, offset + self.vertices_length):
            for loop in vert.link_loops:
                face = loop.face.index
                bm.faces[face].material_index = cpt_index_mat
    cpt_index_mat += 1
    offset = offset + self.vertices_length
    return offset, cpt_index_mat