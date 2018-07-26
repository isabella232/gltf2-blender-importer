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

def create_blender_cycles(gltf_pbr, mat_name):
    material = bpy.data.materials[mat_name]
    material.use_nodes = True
    node_tree = material.node_tree

    # delete all nodes except output
    for node in list(node_tree.nodes):
        if not node.type == 'OUTPUT_MATERIAL':
            node_tree.nodes.remove(node)

    output_node = node_tree.nodes[0]
    output_node.location = 1000,0

    # create PBR node
    principled = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = 0,0

    if gltf_pbr.color_type == gltf_pbr.SIMPLE:

        if not gltf_pbr.vertex_color:

            # change input values
            principled.inputs[0].default_value = gltf_pbr.baseColorFactor
            principled.inputs[5].default_value = gltf_pbr.metallicFactor #TODO : gltf_pbrly set metallic & specular in same way
            principled.inputs[7].default_value = gltf_pbr.roughnessFactor

        else:
            # Create attribute node to get COLOR_0 data
            attribute_node = node_tree.nodes.new('ShaderNodeAttribute')
            attribute_node.attribute_name = 'COLOR_0'
            attribute_node.location = -500,0

            principled.inputs[5].default_value = gltf_pbr.metallicFactor #TODO : gltf_pbrly set metallic & specular in same way
            principled.inputs[7].default_value = gltf_pbr.roughnessFactor

            # links
            rgb_node = node_tree.nodes.new('ShaderNodeMixRGB')
            rgb_node.blend_type = 'MULTIPLY'
            rgb_node.inputs['Fac'].default_value = 1.0
            rgb_node.inputs['Color1'].default_value = gltf_pbr.baseColorFactor
            node_tree.links.new(rgb_node.inputs['Color2'], attribute_node.outputs[0])
            node_tree.links.new(principled.inputs[0], rgb_node.outputs[0])

    elif gltf_pbr.color_type == gltf_pbr.TEXTURE_FACTOR:

        #TODO alpha ?
        if gltf_pbr.vertex_color:
            # TODO tree locations
            # Create attribute / separate / math nodes
            attribute_node = node_tree.nodes.new('ShaderNodeAttribute')
            attribute_node.attribute_name = 'COLOR_0'

            separate_vertex_color = node_tree.nodes.new('ShaderNodeSeparateRGB')
            math_vc_R = node_tree.nodes.new('ShaderNodeMath')
            math_vc_R.operation = 'MULTIPLY'

            math_vc_G = node_tree.nodes.new('ShaderNodeMath')
            math_vc_G.operation = 'MULTIPLY'

            math_vc_B = node_tree.nodes.new('ShaderNodeMath')
            math_vc_B.operation = 'MULTIPLY'

        blender_texture(gltf_pbr.baseColorTexture)

        # create UV Map / Mapping / Texture nodes / separate & math and combine
        text_node = node_tree.nodes.new('ShaderNodeTexImage')
        text_node.image = bpy.data.images[gltf_pbr.baseColorTexture.image.blender_image_name]
        text_node.location = -1000,500

        combine = node_tree.nodes.new('ShaderNodeCombineRGB')
        combine.location = -250,500

        math_R  = node_tree.nodes.new('ShaderNodeMath')
        math_R.location = -500, 750
        math_R.operation = 'MULTIPLY'
        math_R.inputs[1].default_value = gltf_pbr.baseColorFactor[0]

        math_G  = node_tree.nodes.new('ShaderNodeMath')
        math_G.location = -500, 500
        math_G.operation = 'MULTIPLY'
        math_G.inputs[1].default_value = gltf_pbr.baseColorFactor[1]

        math_B  = node_tree.nodes.new('ShaderNodeMath')
        math_B.location = -500, 250
        math_B.operation = 'MULTIPLY'
        math_B.inputs[1].default_value = gltf_pbr.baseColorFactor[2]

        separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
        separate.location = -750, 500

        mapping = node_tree.nodes.new('ShaderNodeMapping')
        mapping.location = -1500, 500

        uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        uvmap.location = -2000, 500
        uvmap["gltf2_texcoord"] = gltf_pbr.baseColorTexture.texcoord # Set custom flag to retrieve TexCoord
        # UV Map will be set after object/UVMap creation

        # Create links
        if gltf_pbr.vertex_color:
            node_tree.links.new(separate_vertex_color.inputs[0], attribute_node.outputs[0])
            node_tree.links.new(math_vc_R.inputs[1], separate_vertex_color.outputs[0])
            node_tree.links.new(math_vc_G.inputs[1], separate_vertex_color.outputs[1])
            node_tree.links.new(math_vc_B.inputs[1], separate_vertex_color.outputs[2])
            node_tree.links.new(math_vc_R.inputs[0], math_R.outputs[0])
            node_tree.links.new(math_vc_G.inputs[0], math_G.outputs[0])
            node_tree.links.new(math_vc_B.inputs[0], math_B.outputs[0])
            node_tree.links.new(combine.inputs[0], math_vc_R.outputs[0])
            node_tree.links.new(combine.inputs[1], math_vc_G.outputs[0])
            node_tree.links.new(combine.inputs[2], math_vc_B.outputs[0])

        else:
            node_tree.links.new(combine.inputs[0], math_R.outputs[0])
            node_tree.links.new(combine.inputs[1], math_G.outputs[0])
            node_tree.links.new(combine.inputs[2], math_B.outputs[0])

        # Common for both mode (non vertex color / vertex color)
        node_tree.links.new(math_R.inputs[0], separate.outputs[0])
        node_tree.links.new(math_G.inputs[0], separate.outputs[1])
        node_tree.links.new(math_B.inputs[0], separate.outputs[2])

        node_tree.links.new(mapping.inputs[0], uvmap.outputs[0])
        node_tree.links.new(text_node.inputs[0], mapping.outputs[0])
        node_tree.links.new(separate.inputs[0], text_node.outputs[0])


        node_tree.links.new(principled.inputs[0], combine.outputs[0])

    elif gltf_pbr.color_type == gltf_pbr.TEXTURE:

        blender_texture(gltf_pbr.baseColorTexture)

        #TODO alpha ?
        if gltf_pbr.vertex_color:
            # Create attribute / separate / math nodes
            attribute_node = node_tree.nodes.new('ShaderNodeAttribute')
            attribute_node.attribute_name = 'COLOR_0'
            attribute_node.location = -2000,250

            separate_vertex_color = node_tree.nodes.new('ShaderNodeSeparateRGB')
            separate_vertex_color.location = -1500, 250

            math_vc_R = node_tree.nodes.new('ShaderNodeMath')
            math_vc_R.operation = 'MULTIPLY'
            math_vc_R.location = -1000,750

            math_vc_G = node_tree.nodes.new('ShaderNodeMath')
            math_vc_G.operation = 'MULTIPLY'
            math_vc_G.location = -1000,500

            math_vc_B = node_tree.nodes.new('ShaderNodeMath')
            math_vc_B.operation = 'MULTIPLY'
            math_vc_B.location = -1000,250


            combine = node_tree.nodes.new('ShaderNodeCombineRGB')
            combine.location = -500,500

            separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
            separate.location = -1500, 500

        # create UV Map / Mapping / Texture nodes / separate & math and combine
        text_node = node_tree.nodes.new('ShaderNodeTexImage')
        text_node.image = bpy.data.images[gltf_pbr.baseColorTexture.image.blender_image_name]
        if gltf_pbr.vertex_color:
            text_node.location = -2000,500
        else:
            text_node.location = -500,500

        mapping = node_tree.nodes.new('ShaderNodeMapping')
        if gltf_pbr.vertex_color:
            mapping.location = -2500,500
        else:
            mapping.location = -1500,500

        uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        if gltf_pbr.vertex_color:
            uvmap.location = -3000,500
        else:
            uvmap.location = -2000,500
        uvmap["gltf2_texcoord"] = gltf_pbr.baseColorTexture.texcoord # Set custom flag to retrieve TexCoord
        # UV Map will be set after object/UVMap creation

        # Create links
        if gltf_pbr.vertex_color:
            node_tree.links.new(separate_vertex_color.inputs[0], attribute_node.outputs[0])

            node_tree.links.new(math_vc_R.inputs[1], separate_vertex_color.outputs[0])
            node_tree.links.new(math_vc_G.inputs[1], separate_vertex_color.outputs[1])
            node_tree.links.new(math_vc_B.inputs[1], separate_vertex_color.outputs[2])

            node_tree.links.new(combine.inputs[0], math_vc_R.outputs[0])
            node_tree.links.new(combine.inputs[1], math_vc_G.outputs[0])
            node_tree.links.new(combine.inputs[2], math_vc_B.outputs[0])

            node_tree.links.new(separate.inputs[0], text_node.outputs[0])

            node_tree.links.new(principled.inputs[0], combine.outputs[0])

            node_tree.links.new(math_vc_R.inputs[0], separate.outputs[0])
            node_tree.links.new(math_vc_G.inputs[0], separate.outputs[1])
            node_tree.links.new(math_vc_B.inputs[0], separate.outputs[2])

        else:
            node_tree.links.new(principled.inputs[0], text_node.outputs[0])

        # Common for both mode (non vertex color / vertex color)

        node_tree.links.new(mapping.inputs[0], uvmap.outputs[0])
        node_tree.links.new(text_node.inputs[0], mapping.outputs[0])


    # Says metallic, but it means metallic & Roughness values
    if gltf_pbr.metallic_type == gltf_pbr.SIMPLE:
        principled.inputs[4].default_value = gltf_pbr.metallicFactor
        principled.inputs[7].default_value = gltf_pbr.roughnessFactor

    elif gltf_pbr.metallic_type == gltf_pbr.TEXTURE:
        blender_texture(gltf_pbr.metallicRoughnessTexture)
        metallic_text = node_tree.nodes.new('ShaderNodeTexImage')
        metallic_text.image = bpy.data.images[gltf_pbr.metallicRoughnessTexture.image.blender_image_name]
        metallic_text.color_space = 'NONE'
        metallic_text.location = -500,0

        metallic_separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
        metallic_separate.location = -250,0

        metallic_mapping = node_tree.nodes.new('ShaderNodeMapping')
        metallic_mapping.location = -1000,0

        metallic_uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        metallic_uvmap.location = -1500,0
        metallic_uvmap["gltf2_texcoord"] = gltf_pbr.metallicRoughnessTexture.texcoord # Set custom flag to retrieve TexCoord

        # links
        node_tree.links.new(metallic_separate.inputs[0], metallic_text.outputs[0])
        node_tree.links.new(principled.inputs[4], metallic_separate.outputs[2]) # metallic
        node_tree.links.new(principled.inputs[7], metallic_separate.outputs[1]) # Roughness

        node_tree.links.new(metallic_mapping.inputs[0], metallic_uvmap.outputs[0])
        node_tree.links.new(metallic_text.inputs[0], metallic_mapping.outputs[0])

    elif gltf_pbr.metallic_type == gltf_pbr.TEXTURE_FACTOR:

        blender_texture(gltf_pbr.metallicRoughnessTexture)

        metallic_text = node_tree.nodes.new('ShaderNodeTexImage')
        metallic_text.image = bpy.data.images[gltf_pbr.metallicRoughnessTexture.image.blender_image_name]
        metallic_text.color_space = 'NONE'
        metallic_text.location = -1000,0

        metallic_separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
        metallic_separate.location = -500,0

        metallic_math     = node_tree.nodes.new('ShaderNodeMath')
        metallic_math.operation = 'MULTIPLY'
        metallic_math.inputs[1].default_value = gltf_pbr.metallicFactor
        metallic_math.location = -250,100

        roughness_math = node_tree.nodes.new('ShaderNodeMath')
        roughness_math.operation = 'MULTIPLY'
        roughness_math.inputs[1].default_value = gltf_pbr.roughnessFactor
        roughness_math.location = -250,-100

        metallic_mapping = node_tree.nodes.new('ShaderNodeMapping')
        metallic_mapping.location = -1000,0

        metallic_uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        metallic_uvmap.location = -1500,0
        metallic_uvmap["gltf2_texcoord"] = gltf_pbr.metallicRoughnessTexture.texcoord # Set custom flag to retrieve TexCoord


        # links
        node_tree.links.new(metallic_separate.inputs[0], metallic_text.outputs[0])

        # metallic
        node_tree.links.new(metallic_math.inputs[0], metallic_separate.outputs[2])
        node_tree.links.new(principled.inputs[4], metallic_math.outputs[0])

        # roughness
        node_tree.links.new(roughness_math.inputs[0], metallic_separate.outputs[1])
        node_tree.links.new(principled.inputs[7], roughness_math.outputs[0])

        node_tree.links.new(metallic_mapping.inputs[0], metallic_uvmap.outputs[0])
        node_tree.links.new(metallic_text.inputs[0], metallic_mapping.outputs[0])

    # link node to output
    node_tree.links.new(output_node.inputs[0], principled.outputs[0])

def blender_pbr(gltf_pbr, mat_name):
    engine = bpy.context.scene.render.engine
    if engine == 'CYCLES':
        create_blender_cycles(gltf_pbr, mat_name)
    # else:
    #     pass #TODO for internal / Eevee in future 2.8