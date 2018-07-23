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


def get_pbr_node(node_tree):
        pass

def get_output_node(node_tree):
    output = [node for node in node_tree.nodes if node.type == 'OUTPUT_MATERIAL'][0]
    return output

def get_output_surface_input(node_tree):
    output_node = get_output_node(node_tree)
    return output_node.inputs['Surface']

def get_diffuse_texture(node_tree):
    for node in node_tree.nodes:
        print(node.name)
        if node.label == 'BASE COLOR':
            return node

    return None

def get_preoutput_node_output(node_tree):
    output_node = get_output_node(node_tree)
    preoutput_node = output_node.inputs['Surface'].links[0].from_node

    # Pre output node is Principled BSDF or any BSDF => BSDF
    if 'BSDF' in preoutput_node.type:
        return preoutput_node.outputs['BSDF']
    elif 'SHADER' in preoutput_node.type:
        return preoutput_node.outputs['Shader']
    else:
        print(preoutput_node.type)


    # Pre output node is MixShader => Shader

# def blender_texture(current):
#         blender_image(current.image)

# def create_blender_cycles(current, mat_name):
#         material = bpy.data.materials[mat_name]
#         node_tree = material.node_tree

#         blender_texture(current.texture)

#         # retrieve principled node and output node
#         principled = [node for node in node_tree.nodes if node.type == "BSDF_PRINCIPLED"][0]
#         output = [node for node in node_tree.nodes if node.type == 'OUTPUT_MATERIAL'][0]

#         # add nodes
#         emit = node_tree.nodes.new('ShaderNodeEmission')
#         emit.location = 0,1000
#         separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
#         separate.location = -750, 1000
#         combine = node_tree.nodes.new('ShaderNodeCombineRGB')
#         combine.location = -250, 1000
#         mapping = node_tree.nodes.new('ShaderNodeMapping')
#         mapping.location = -1500, 1000
#         uvmap = node_tree.nodes.new('ShaderNodeUVMap')
#         uvmap.location = -2000,1000
#         uvmap["gltf2_texcoord"] = current.texCoord # Set custom flag to retrieve TexCoord

#         text  = node_tree.nodes.new('ShaderNodeTexImage')
#         text.image = bpy.data.images[current.texture.image.blender_image_name]
#         text.location = -1000,1000
#         add = node_tree.nodes.new('ShaderNodeAddShader')
#         add.location = 500,500

#         math_R  = node_tree.nodes.new('ShaderNodeMath')
#         math_R.location = -500, 1500
#         math_R.operation = 'MULTIPLY'
#         math_R.inputs[1].default_value = current.factor[0]

#         math_G  = node_tree.nodes.new('ShaderNodeMath')
#         math_G.location = -500, 1250
#         math_G.operation = 'MULTIPLY'
#         math_G.inputs[1].default_value = current.factor[1]

#         math_B  = node_tree.nodes.new('ShaderNodeMath')
#         math_B.location = -500, 1000
#         math_B.operation = 'MULTIPLY'
#         math_B.inputs[1].default_value = current.factor[2]

#         # create links
#         node_tree.links.new(mapping.inputs[0], uvmap.outputs[0])
#         node_tree.links.new(text.inputs[0], mapping.outputs[0])
#         node_tree.links.new(separate.inputs[0], text.outputs[0])
#         node_tree.links.new(math_R.inputs[0], separate.outputs[0])
#         node_tree.links.new(math_G.inputs[0], separate.outputs[1])
#         node_tree.links.new(math_B.inputs[0], separate.outputs[2])
#         node_tree.links.new(combine.inputs[0], math_R.outputs[0])
#         node_tree.links.new(combine.inputs[1], math_G.outputs[0])
#         node_tree.links.new(combine.inputs[2], math_B.outputs[0])
#         node_tree.links.new(emit.inputs[0], combine.outputs[0])

#         # following  links will modify PBR node tree
#         node_tree.links.new(add.inputs[0], emit.outputs[0])
#         node_tree.links.new(add.inputs[1], principled.outputs[0])
#         node_tree.links.new(output.inputs[0], add.outputs[0])
