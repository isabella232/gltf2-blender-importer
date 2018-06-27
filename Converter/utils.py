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

from mathutils import Matrix, Vector, Quaternion

class Conversion():
    def get_node_matrix(gltf_node):
        if hasattr(gltf_node, 'matrix'):
            return Conversion.matrix(gltf_node.matrix)
        else:
            return Conversion.matrix_from_trs(gltf_node.translation, gltf_node.rotation, gltf_node.scale)

    def matrix_from_trs(translation, rotation, scale):
        mat = Matrix([
            [scale[0], 0, 0, 0],
            [0, scale[1], 0, 0],
            [0, 0, scale[2], 0],
            [0, 0, 0, 1]
        ])

        mat = Conversion.matrix_quaternion(rotation).to_matrix().to_4x4() * mat
        mat = Matrix.Translation(Vector(Conversion.location(translation))) * mat

        return mat

    @staticmethod
    def matrix(mat_input):
        mat_input =  Matrix([mat_input[0:4], mat_input[4:8], mat_input[8:12], mat_input[12:16]])
        mat_input.transpose()

        s = mat_input.to_scale()
        rotation = mat_input.to_quaternion()
        location = mat_input.to_translation()

        return Conversion.matrix_from_trs(location, rotation, s)

    @staticmethod
    def quaternion(q):
        return Quaternion([q[3], q[0], -q[2], q[1]])
    
    @staticmethod    
    def matrix_quaternion(q):
        return Quaternion([q[0], q[1], -q[3], q[2]])
    
    @staticmethod
    def location(location):
        return [location[0], -location[2], location[1]]
    
    @staticmethod
    def scale(scale):
        return scale # TODO test scale animation