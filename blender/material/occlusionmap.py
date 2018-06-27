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
from .texture import *

def create_blender_occlusion_cycles(gltf_occlusion, mat_name):
    # Pack texture, but doesn't use it for now. Occlusion is calculated from Cycles.
 #    material = bpy.data.materials[mat_name]
 #    node_tree = material.node_tree

 #    blender_texture(gltf_occlusion.texture)
 #    principled = [node for node in node_tree.nodes if node.type == "BSDF_PRINCIPLED"][0]

 #    #add nodes (SECURIZE this)
 #    diffuse_input = principled.inputs['Base Color']
 #    diffuse = diffuse_input.links[0].from_node
 #    l = principled.inputs['Base Color'].links[0]


 #    # occlusion texture
 #    occlusion = node_tree.nodes.new('ShaderNodeTexImage')
 #    mixrgb = node_tree.nodes.new('ShaderNodeMixRGB')

	# mapping = node_tree.nodes.new('ShaderNodeMapping')
 #    mapping.location = -1000,-500
 # Link diffuse to mix shader
 #	  node_tree.links.new(diffuse.outputs['Image'], mixrgb.inputs['Color1'])
 # 	  node_tree.links.remove(l)

    # bpy.data.images[gltf_occlusion.texture.image.blender_image_name].use_fake_user = True
    pass

def blender_occlusion(gltf_occlusion, mat_name):
    engine = bpy.context.scene.render.engine
    if engine == 'CYCLES':
        create_blender_occlusion_cycles(gltf_occlusion, mat_name)
    else:
        pass #TODO for internal / Eevee in future 2.8