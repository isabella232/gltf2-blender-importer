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

from mathutils import Matrix, Vector, Quaternion

def blender_node(current, parent):
    def set_transforms(current, obj):
        if parent is None:
            obj.matrix_world =  self.transform
            return

        for node in self.gltf.scene.nodes.values(): # TODO if parent is in another scene
            if node.index == parent:
                if node.is_joint == True:
                    delta = Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0))
                    obj.matrix_world = self.transform * delta.inverted().to_matrix().to_4x4()
                    return
                else:
                    obj.matrix_world = self.transform
                    return

    def set_blender_parent(current, obj, parent):
        self.parent = parent
        if self.mesh:
            if self.name:
                self.gltf.log.info("Blender create Mesh node " + self.name)
            else:
                self.gltf.log.info("Blender create Mesh node")

            if self.name:
                name = self.name
            else:
                # Take mesh name if exist
                if self.mesh.name:
                    name = self.mesh.name
                else:
                    name = "Object_" + str(self.index)

            mesh = self.mesh.blender_create(parent)

            obj = bpy.data.objects.new(name, mesh)
            obj.rotation_mode = 'QUATERNION'
            bpy.data.scenes[self.gltf.blender.scene].objects.link(obj)
            self.set_transforms(obj, parent)
            self.blender_object = obj.name
            self.set_blender_parent(obj, parent)

            self.mesh.blender_set_mesh(mesh, obj)

            for child in self.children:
                child.blender_create(self.index)

            return

        if self.camera:
            if self.name:
                self.gltf.log.info("Blender create Camera node " + self.name)
            else:
                self.gltf.log.info("Blender create Camera node")
            obj = self.camera.create_blender()
            self.set_transforms(obj, parent) #TODO default rotation of cameras ?
            self.blender_object = obj.name
            self.set_blender_parent(obj, parent)

            return


        if self.is_joint:
            if self.name:
                self.gltf.log.info("Blender create Bone node " + self.name)
            else:
                self.gltf.log.info("Blender create Bone node")
            # Check if corresponding armature is already created, create it if needed
            if self.gltf.skins[self.skin_id].blender_armature_name is None:
                self.gltf.skins[self.skin_id].create_blender_armature(parent)

            self.gltf.skins[self.skin_id].create_bone(self, parent)

            for child in self.children:
                child.blender_create(self.index)

            return

        # No mesh, no camera. For now, create empty #TODO

        if self.name:
            self.gltf.log.info("Blender create Empty node " + self.name)
            obj = bpy.data.objects.new(self.name, None)
        else:
            self.gltf.log.info("Blender create Empty node")
            obj = bpy.data.objects.new("Node", None)
        obj.rotation_mode = 'QUATERNION'
        bpy.data.scenes[self.gltf.blender.scene].objects.link(obj)
        self.set_transforms(obj, parent)
        self.blender_object = obj.name
        self.set_blender_parent(obj, parent)

        for child in self.children:
            child.blender_create(self.index)




