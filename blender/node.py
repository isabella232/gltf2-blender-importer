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
 
 #DONE

import bpy
from .utils import Conversion
from .mesh import *
from .rig import *

from mathutils import Matrix, Vector, Quaternion

def blender_node(gltf_node, parent, blender_scene):
    def set_transforms(gltf_node, obj, parent):
        obj.rotation_mode = 'QUATERNION'
        if hasattr(gltf_node, 'matrix'):
            obj.matrix_world = Conversion.matrix(gltf_node.matrix)
        elif gltf_node.is_joint:
            delta = Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0))
            obj.matrix_world = Conversion.get_node_matrix(gltf_node) * delta.inverted().to_matrix().to_4x4()
        else:
            obj.location = Conversion.location(gltf_node.translation)
            obj.rotation_quaternion = Conversion.quaternion(gltf_node.rotation)
            obj.scale = Conversion.scale(gltf_node.scale)

    def set_blender_parent(gltf_node, obj, parent):
        pass
        if parent is None:
            return

        for node in gltf_node.gltf.scene.nodes.values(): # TODO if parent is in another scene
            if node.index == parent:
                if node.is_joint == True:
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects[node.blender_armature_name].select = True
                    bpy.context.scene.objects.active = bpy.data.objects[node.blender_armature_name]
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.data.objects[node.blender_armature_name].data.edit_bones.active = bpy.data.objects[node.blender_armature_name].data.edit_bones[node.blender_bone_name]
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select = True
                    bpy.data.objects[node.blender_armature_name].select = True
                    bpy.context.scene.objects.active = bpy.data.objects[node.blender_armature_name]
                    bpy.ops.object.parent_set(type='BONE', keep_transform=True)

                    return
                if node.blender_object:
                    obj.parent = bpy.data.objects[node.blender_object]
                    return

        gltf_node.gltf.log.error("ERROR, parent not found")

    gltf_node.parent = parent
    if gltf_node.mesh:
        if gltf_node.name:
            gltf_node.gltf.log.info("Blender create Mesh node " + gltf_node.name)
        else:
            gltf_node.gltf.log.info("Blender create Mesh node")

        if gltf_node.name:
            name = gltf_node.name
        else:
            # Take mesh name if exist
            if gltf_node.mesh.name:
                name = gltf_node.mesh.name
            else:
                name = "Object_" + str(gltf_node.index)

        mesh = blender_mesh(gltf_node.mesh, parent)

        obj = bpy.data.objects.new(name, mesh)
        bpy.data.scenes[blender_scene].objects.link(obj)
        set_transforms(gltf_node, obj, parent)
        gltf_node.blender_object = obj.name
        set_blender_parent(gltf_node, obj, parent)

        blender_set_mesh(gltf_node.mesh, mesh, obj)

        for child in gltf_node.children:
            blender_node(child, gltf_node.index, blender_scene)

        return

    # if gltf_node.camera:
    #     if gltf_node.name:
    #         gltf_node.gltf.log.info("Blender create Camera node " + gltf_node.name)
    #     else:
    #         gltf_node.gltf.log.info("Blender create Camera node")
    #     obj = gltf_node.camera.create_blender()
    #     set_transforms(gltf_node, obj, parent) #TODO default rotation of cameras ?
    #     gltf_node.blender_object = obj.name
    #     set_blender_parent(gltf_node, obj, parent)

    #     return


    if gltf_node.is_joint:
        if gltf_node.name:
            gltf_node.gltf.log.info("Blender create Bone node " + gltf_node.name)
        else:
            gltf_node.gltf.log.info("Blender create Bone node")
        # Check if corresponding armature is already created, create it if needed
        if not hasattr(gltf_node.gltf.skins[gltf_node.skin_id], 'blender_armature_name'):
            # FIXME (AurL) this is dirty
            gltf_node.gltf.skins[gltf_node.skin_id].blender_scene = blender_scene
            blender_armature(gltf_node.gltf.skins[gltf_node.skin_id], parent)

        blender_bone(gltf_node.gltf.skins[gltf_node.skin_id], gltf_node, parent)

        for child in gltf_node.children:
            blender_node(child, gltf_node.index, blender_scene)

        return

    # No mesh, no camera. For now, create empty #TODO
    if gltf_node.name:
        gltf_node.gltf.log.info("Blender create Empty node " + gltf_node.name)
        obj = bpy.data.objects.new(gltf_node.name, None)
    else:
        gltf_node.gltf.log.info("Blender create Empty node")
        obj = bpy.data.objects.new("Node", None)

    bpy.data.scenes[blender_scene].objects.link(obj)
    set_transforms(gltf_node, obj, parent)
    gltf_node.blender_object = obj.name
    set_blender_parent(gltf_node, obj, parent)

    for child in gltf_node.children:
        blender_node(child, gltf_node.index, blender_scene)

    return obj




