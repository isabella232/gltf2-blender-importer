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
 
import logging

class Log():
    def __init__(self, loglevel):
        self.logger = logging.getLogger('glTFImporter')
        self.hdlr = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.hdlr.setFormatter(formatter)
        self.logger.addHandler(self.hdlr)
        self.logger.setLevel(int(loglevel))

    def getLevels():
        levels = [
        (str(logging.CRITICAL), "Critical", "", logging.CRITICAL),
        (str(logging.ERROR), "Error", "", logging.ERROR),
        (str(logging.WARNING), "Warning", "", logging.WARNING),
        (str(logging.INFO), "Info", "", logging.INFO),
        (str(logging.NOTSET), "NotSet", "", logging.NOTSET)
        ]

        return levels

    def default():
        return str(logging.ERROR)
