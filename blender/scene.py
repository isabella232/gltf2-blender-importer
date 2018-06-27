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
from .animation import *

def blender_scene(gltf_scene):
    # Create a new scene only if not already exists in .blend file
    # TODO : put in current scene instead ?
        if gltf_scene.name not in [scene.name for scene in bpy.data.scenes]:
            if gltf_scene.name:
                scene = bpy.data.scenes.new(gltf_scene.name)
            else:
                scene = bpy.data.scenes.new('Scene')
            scene.render.engine = "CYCLES"

            gltf_scene.gltf.blender.set_scene(scene.name)
        else:
            gltf_scene.gltf.blender.set_scene(gltf_scene.name)
        for node in gltf_scene.nodes.values():
            if node.root:
                blender_node(node, None) # None => No parent

        # Now that all mesh / bones are created, create vertex groups on mesh
        for armature in gltf_scene.gltf.skins.values():
            create_vertex_groups(armature)

        for armature in gltf_scene.gltf.skins.values():
            assign_vertex_groups(armature)

        for armature in gltf_scene.gltf.skins.values():
            create_armature_modifiers(armature)

        for node in gltf_scene.nodes.values():
            if node.root:
                blender_animation(node.animation)


    # TODO create blender for other scenes
