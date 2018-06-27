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
from .node import *

def blender_scene(gltf_scene):
    # Create a new scene only if not already exists in .blend file
    # TODO : put in current scene instead ?
        if self.name not in [scene.name for scene in bpy.data.scenes]:
            if self.name:
                scene = bpy.data.scenes.new(self.name)
            else:
                scene = bpy.data.scenes.new('Scene')
            scene.render.engine = "CYCLES"

            self.gltf.blender.set_scene(scene.name)
        else:
            self.gltf.blender.set_scene(self.name)

        for node in self.nodes.values():
            if node.root:
                node.blender_create(None) # None => No parent

        # Now that all mesh / bones are created, create vertex groups on mesh
        for armature in self.gltf.skins.values():
            armature.create_vertex_groups()

        for armature in self.gltf.skins.values():
            armature.assign_vertex_groups()

        for armature in self.gltf.skins.values():
            armature.create_armature_modifiers()

        for node in self.nodes.values():
            if node.root:
                node.animation.blender_anim()


    # TODO create blender for other scenes
