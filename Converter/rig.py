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
from .utils import Conversion
from mathutils import Vector, Matrix, Quaternion

def blender_armature(gltf_skin, parent):
    if gltf_skin.name is not None:
        name = gltf_skin.name
    else:
        name = "Armature_" + str(gltf_skin.index)

    armature = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, armature)
    bpy.data.scenes[gltf_skin.blender_scene].objects.link(obj)
    gltf_skin.blender_armature_name = obj.name
    if parent:
        obj.parent = bpy.data.objects[gltf_skin.gltf.scene.nodes[parent].blender_object]


def set_bone_transforms(gltf_bone, bone, node, parent):
    obj   = bpy.data.objects[gltf_bone.blender_armature_name]
    delta = Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0))

    mat = Matrix()
    transform = Conversion.get_node_matrix(node)

    if not parent:
        mat = transform * delta.to_matrix().to_4x4()
    else:
        if not gltf_bone.gltf.scene.nodes[parent].is_joint: # TODO if Node in another scene
            mat = transform * delta.to_matrix().to_4x4()
        else:
            parent_mat = obj.data.edit_bones[gltf_bone.gltf.scene.nodes[parent].blender_bone_name].matrix # Node in another scene

            mat = (parent_mat.to_quaternion() * delta.inverted() * transform.to_quaternion() * delta).to_matrix().to_4x4()
            mat = Matrix.Translation(parent_mat.to_translation() + ( parent_mat.to_quaternion() * delta.inverted() * transform.to_translation() )) * mat
            #TODO scaling of bones

    bone.matrix = mat
    return bone.matrix

def blender_bone(gltf_bone, node, parent):
    scene = bpy.data.scenes[gltf_bone.blender_scene]
    obj   = bpy.data.objects[gltf_bone.blender_armature_name]

    bpy.context.screen.scene = scene
    scene.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")

    if node.name:
        name = node.name
    else:
        name = "Bone_" + str(node.index)

    bone = obj.data.edit_bones.new(name)
    node.blender_bone_name = bone.name
    node.blender_armature_name = gltf_bone.blender_armature_name
    bone.tail = Vector((0.0,1.0,0.0)) # Needed to keep bone alive
    mat = set_bone_transforms(gltf_bone, bone, node, parent)
    node.blender_bone_matrix = mat

    # Set parent
    if parent is not None and hasattr(gltf_bone.gltf.scene.nodes[parent], "blender_bone_name"):
        bone.parent = obj.data.edit_bones[gltf_bone.gltf.scene.nodes[parent].blender_bone_name] #TODO if in another scene

    bpy.ops.object.mode_set(mode="OBJECT")

def create_vertex_groups(gltf_skin, mesh_id):
    obj = bpy.data.objects[gltf_skin.gltf.scene.nodes[mesh_id].blender_object]

    for bone in gltf_skin.bones:
        obj.vertex_groups.new(gltf_skin.gltf.scene.nodes[bone].blender_bone_name)

def assign_vertex_groups(gltf_skin, mesh_id):
    node = gltf_skin.gltf.scene.nodes[mesh_id]
    obj = bpy.data.objects[node.blender_object]

    offset = 0
    for prim in node.mesh.primitives:
        if 'JOINTS_0' in prim.attributes.keys() and 'WEIGHTS_0' in prim.attributes.keys():

            joint_ = prim.attributes['JOINTS_0']['result']
            weight_ = prim.attributes['WEIGHTS_0']['result']

            for poly in obj.data.polygons:
                for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    vert_idx = obj.data.loops[loop_idx].vertex_index
                    if vert_idx in range(offset, offset + prim.vertices_length):

                        if offset != 0:
                            tab_index = vert_idx % offset
                        else:
                            tab_index = vert_idx

                        cpt = 0
                        for joint_idx in joint_[tab_index]:
                            weight_val = weight_[tab_index][cpt]
                            if weight_val != 0.0:   # It can be a problem to assign weights of 0
                                                    # for bone index 0, if there is always 4 indices in joint_ tuple
                                group = obj.vertex_groups[gltf_skin.gltf.scene.nodes[gltf_skin.bones[joint_idx]].blender_bone_name]
                                group.add([vert_idx], weight_val, 'REPLACE')
                            cpt += 1
        else:
            gltf_skin.gltf.log.error("No Skinning ?????") #TODO


        offset = offset + prim.vertices_length

def create_armature_modifiers(gltf_skin, mesh_id):
    node = gltf_skin.gltf.scene.nodes[mesh_id]
    obj = bpy.data.objects[node.blender_object]

    for obj_sel in bpy.context.scene.objects:
        obj_sel.select = False
    obj.select = True
    bpy.context.scene.objects.active = obj

    #bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    #obj.parent = bpy.data.objects[gltf_skin.blender_armature_name]
    arma = obj.modifiers.new(name="Armature", type="ARMATURE")
    arma.object = bpy.data.objects[gltf_skin.blender_armature_name]