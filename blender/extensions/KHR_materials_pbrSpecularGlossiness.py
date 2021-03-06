import bpy
from ..material.texture import *

def create_blender_specular(gltf_specular, mat_name):
    material = bpy.data.materials[mat_name]
    material.use_nodes = True
    node_tree = material.node_tree

    # delete all nodes except output
    for node in list(node_tree.nodes):
        if not node.type == 'OUTPUT_MATERIAL':
            node_tree.nodes.remove(node)

    output_node = node_tree.nodes[0]
    output_node.location = 1250,0

    # create PBR node
    diffuse    = node_tree.nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = 0,0
    glossy     = node_tree.nodes.new('ShaderNodeBsdfGlossy')
    glossy.location  = 0,100
    mix        = node_tree.nodes.new('ShaderNodeMixShader')
    mix.location     = 500,0

    glossy.inputs[1].default_value = 1 - gltf_specular.glossinessFactor

    if gltf_specular.diffuse_type == gltf_specular.SIMPLE:
        if not gltf_specular.vertex_color:
            # change input values
            diffuse.inputs[0].default_value = gltf_specular.diffuseFactor

        else:
            # Create attribute node to get COLOR_0 data
            attribute_node = node_tree.nodes.new('ShaderNodeAttribute')
            attribute_node.attribute_name = 'COLOR_0'
            attribute_node.location = -500,0

            # links
            node_tree.links.new(diffuse.inputs[0], attribute_node.outputs[1])

    elif gltf_specular.diffuse_type == gltf_specular.TEXTURE_FACTOR:

        #TODO alpha ?
        if gltf_specular.vertex_color:
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

        blender_texture(gltf_specular.diffuseTexture)

        # create UV Map / Mapping / Texture nodes / separate & math and combine
        text_node = node_tree.nodes.new('ShaderNodeTexImage')
        text_node.image = bpy.data.images[gltf_specular.diffuseTexture.image.blender_image_name]
        text_node.label = 'BASE COLOR'
        text_node.location = -1000,500

        combine = node_tree.nodes.new('ShaderNodeCombineRGB')
        combine.location = -250,500

        math_R  = node_tree.nodes.new('ShaderNodeMath')
        math_R.location = -500, 750
        math_R.operation = 'MULTIPLY'
        math_R.inputs[1].default_value = gltf_specular.diffuseFactor[0]

        math_G  = node_tree.nodes.new('ShaderNodeMath')
        math_G.location = -500, 500
        math_G.operation = 'MULTIPLY'
        math_G.inputs[1].default_value = gltf_specular.diffuseFactor[1]

        math_B  = node_tree.nodes.new('ShaderNodeMath')
        math_B.location = -500, 250
        math_B.operation = 'MULTIPLY'
        math_B.inputs[1].default_value = gltf_specular.diffuseFactor[2]

        separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
        separate.location = -750, 500

        mapping = node_tree.nodes.new('ShaderNodeMapping')
        mapping.location = -1500, 500

        uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        uvmap.location = -2000, 500
        uvmap["gltf2_texcoord"] = gltf_specular.diffuseTexture.texcoord # Set custom flag to retrieve TexCoord
        # UV Map will be set after object/UVMap creation

        # Create links
        if gltf_specular.vertex_color:
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


        node_tree.links.new(diffuse.inputs[0], combine.outputs[0])

    elif gltf_specular.diffuse_type == gltf_specular.TEXTURE:

        blender_texture(gltf_specular.diffuseTexture)

        #TODO alpha ?
        if gltf_specular.vertex_color:
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
        text_node.image = bpy.data.images[gltf_specular.diffuseTexture.image.blender_image_name]
        text_node.label = 'BASE COLOR'
        if gltf_specular.vertex_color:
            text_node.location = -2000,500
        else:
            text_node.location = -500,500

        mapping = node_tree.nodes.new('ShaderNodeMapping')
        if gltf_specular.vertex_color:
            mapping.location = -2500,500
        else:
            mapping.location = -1500,500

        uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        if gltf_specular.vertex_color:
            uvmap.location = -3000,500
        else:
            uvmap.location = -2000,500
        uvmap["gltf2_texcoord"] = gltf_specular.diffuseTexture.texcoord # Set custom flag to retrieve TexCoord
        # UV Map will be set after object/UVMap creation

        # Create links
        if gltf_specular.vertex_color:
            node_tree.links.new(separate_vertex_color.inputs[0], attribute_node.outputs[0])

            node_tree.links.new(math_vc_R.inputs[1], separate_vertex_color.outputs[0])
            node_tree.links.new(math_vc_G.inputs[1], separate_vertex_color.outputs[1])
            node_tree.links.new(math_vc_B.inputs[1], separate_vertex_color.outputs[2])

            node_tree.links.new(combine.inputs[0], math_vc_R.outputs[0])
            node_tree.links.new(combine.inputs[1], math_vc_G.outputs[0])
            node_tree.links.new(combine.inputs[2], math_vc_B.outputs[0])

            node_tree.links.new(separate.inputs[0], text_node.outputs[0])

            node_tree.links.new(diffuse.inputs[0], combine.outputs[0])

            node_tree.links.new(math_vc_R.inputs[0], separate.outputs[0])
            node_tree.links.new(math_vc_G.inputs[0], separate.outputs[1])
            node_tree.links.new(math_vc_B.inputs[0], separate.outputs[2])

        else:
            node_tree.links.new(diffuse.inputs[0], text_node.outputs[0])

        # Common for both mode (non vertex color / vertex color)

        node_tree.links.new(mapping.inputs[0], uvmap.outputs[0])
        node_tree.links.new(text_node.inputs[0], mapping.outputs[0])


    if gltf_specular.specgloss_type == gltf_specular.SIMPLE:

        combine = node_tree.nodes.new('ShaderNodeCombineRGB')
        combine.inputs[0].default_value = gltf_specular.specularFactor[0]
        combine.inputs[1].default_value = gltf_specular.specularFactor[1]
        combine.inputs[2].default_value = gltf_specular.specularFactor[2]

        # links
        node_tree.links.new(glossy.inputs[0], combine.outputs[0])

    elif gltf_specular.specgloss_type == gltf_specular.TEXTURE:
        blender_texture(gltf_specular.specularGlossinessTexture)
        spec_text = node_tree.nodes.new('ShaderNodeTexImage')
        spec_text.image = bpy.data.images[gltf_specular.specularGlossinessTexture.image.blender_image_name]
        spec_text.color_space = 'NONE'
        spec_text.location = -500,0

        spec_mapping = node_tree.nodes.new('ShaderNodeMapping')
        spec_mapping.location = -1000,0

        spec_uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        spec_uvmap.location = -1500,0
        spec_uvmap["gltf2_texcoord"] = gltf_specular.specularGlossinessTexture.texcoord # Set custom flag to retrieve TexCoord

        # Invert glossiness and plug it into Glossy BSDF Roughness
        gloss_invert = node_tree.nodes.new('ShaderNodeInvert')
        gloss_invert.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)
        node_tree.links.new(spec_text.outputs['Alpha'], gloss_invert.inputs[0])

        # links
        node_tree.links.new(glossy.inputs[0], gloss_invert.outputs[0])
        node_tree.links.new(mix.inputs[0], spec_text.outputs[1])

        node_tree.links.new(spec_mapping.inputs[0], spec_uvmap.outputs[0])
        node_tree.links.new(spec_text.inputs[0], spec_mapping.outputs[0])

    elif gltf_specular.specgloss_type == gltf_specular.TEXTURE_FACTOR:

        blender_texture(gltf_specular.specularGlossinessTexture)

        spec_text = node_tree.nodes.new('ShaderNodeTexImage')
        spec_text.image = bpy.data.images[gltf_specular.specularGlossinessTexture.image.blender_image_name]
        spec_text.color_space = 'NONE'
        spec_text.location = -1000,0

        # Invert glossiness and plug it into Glossy BSDF Roughness
        gloss_invert = node_tree.nodes.new('ShaderNodeInvert')
        gloss_invert.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)
        node_tree.links.new(spec_text.outputs['Alpha'], gloss_invert.inputs[0])

        spec_math = node_tree.nodes.new('ShaderNodeMath')
        spec_math.operation = 'MULTIPLY'
        spec_math.inputs[0].default_value = gltf_specular.glossinessFactor
        spec_math.location = -250,100

        spec_mapping = node_tree.nodes.new('ShaderNodeMapping')
        spec_mapping.location = -1000,0

        spec_uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        spec_uvmap.location = -1500,0
        spec_uvmap["gltf2_texcoord"] = gltf_specular.specularGlossinessTexture.texcoord # Set custom flag to retrieve TexCoord


        # links
        node_tree.links.new(spec_math.inputs[1], gloss_invert.outputs[0])
        node_tree.links.new(mix.inputs[0], spec_text.outputs[1])
        node_tree.links.new(glossy.inputs[1], spec_math.outputs[0])
        node_tree.links.new(glossy.inputs[0], spec_text.outputs[0])

        node_tree.links.new(spec_mapping.inputs[0], spec_uvmap.outputs[0])
        node_tree.links.new(spec_text.inputs[0], spec_mapping.outputs[0])

    # link node to output
    node_tree.links.new(mix.inputs[2], diffuse.outputs[0])
    node_tree.links.new(mix.inputs[1], glossy.outputs[0])
    node_tree.links.new(output_node.inputs[0], mix.outputs[0])

def blender_pbr_specular(gltf, mat_name):
        engine = bpy.context.scene.render.engine
        if engine == 'CYCLES':
            create_blender_specular(gltf.KHR_materials_pbrSpecularGlossiness, mat_name)
        else:
            pass #TODO for internal / Eevee in future 2.8