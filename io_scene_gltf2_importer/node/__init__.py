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

from ..mesh import *
from ..camera import *
from ..animation import *

class Node():
    def __init__(self, index, json, gltf, root, scene):
        self.index = index
        self.json = json   # Node json
        self.gltf = gltf # Reference to global glTF instance
        self.root = root
        self.scene = scene # Reference to scene
        self.mesh = None
        self.camera = None
        self.children = []
        self.animation = AnimationData(self, self.gltf)
        self.is_joint = False
        self.parent = None

    def read(self):
        if 'name' in self.json.keys():
            self.name = self.json['name']
            self.gltf.log.info("Node " + self.json['name'])
        else:
            self.name = None
            self.gltf.log.info("Node index " + str(self.index))

        self.transform = self.get_transforms()

        if 'mesh' in self.json.keys():
            self.mesh = Mesh(self.json['mesh'], self.gltf.json['meshes'][self.json['mesh']], self.gltf)
            self.mesh.read()
            self.mesh.debug_missing()

            if 'skin' in self.json.keys():
                self.mesh.rig(self.json['skin'], self.index)

        if 'camera' in self.json.keys():
            self.camera = Camera(self.json['camera'], self.name, self.gltf.json['cameras'][self.json['camera']], self.gltf)
            self.camera.read()
            self.camera.debug_missing()


        if not 'children' in self.json.keys():
            return

        for child in self.json['children']:
            child = Node(child, self.gltf.json['nodes'][child], self.gltf, False, self.scene)
            child.read()
            child.debug_missing()
            self.children.append(child)
            self.scene.nodes[child.index] = child

    def get_transforms(self):
        pass

        # if 'matrix' in self.json.keys():
        #     return self.gltf.convert.matrix(self.json['matrix'])

        # mat = Matrix()


        # if 'scale' in self.json.keys():
        #     s = self.json['scale']
        #     mat = Matrix([
        #         [s[0], 0, 0, 0],
        #         [0, s[1], 0, 0],
        #         [0, 0, s[2], 0],
        #         [0, 0, 0, 1]
        #     ])


        # if 'rotation' in self.json.keys():
        #     q = self.gltf.convert.quaternion(self.json['rotation'])
        #     mat = q.to_matrix().to_4x4() * mat

        # if 'translation' in self.json.keys():
        #     mat = Matrix.Translation(Vector(self.gltf.convert.location(self.json['translation']))) * mat

        # return mat

    def debug_missing(self):
        keys = [
                'name',
                'mesh',
                'matrix',
                'translation',
                'rotation',
                'scale',
                'children',
                'camera',
                'skin'
                ]

        for key in self.json.keys():
            if key not in keys:
                self.gltf.log.debug("NODE MISSING " + key)
