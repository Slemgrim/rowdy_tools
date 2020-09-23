# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Rowdy Tools",
    "author": "Markus Raudaschl (CG Rowdy)",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Rowdy Tools",
    "description": "Personal tools for project management",
    "category": "User Interface",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/Slemgrim/rowdy_tools"
}

import bpy
import os
import re
from pathlib import Path
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty


class VIEW3D_PT_rowdy_assets(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Rowdy Tools"
    bl_label = "Asset Management"

    def draw(self, context):
        self.layout.operator_context = 'INVOKE_DEFAULT'
        self.layout.operator('rowdy.backup', text="Backup", icon="NODE_COMPOSITING")
        self.layout.operator('rowdy.promote', text="Promote", icon="EXPORT")
        pass


# -------------------  Backup FUNCTIONS -------------------------

# creates a backup copy of a saved filed with the scheme [filename]_v[x]
# where x is an incremented version number    
class VIEW3D_OT_rowdy_backup(bpy.types.Operator):
    """Creates a backup with incremented version in same folder"""
    bl_idname = "rowdy.backup"
    bl_label = "Backup"

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        path = bpy.path.abspath("//")

        filename = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0]

        files = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            files = [os.path.splitext(filename)[0] for filename in filenames]

        highest_version = 0
        for file in files:
            file = os.path.splitext(file)[0]
            found = re.findall('^' + filename + addon_prefs.backup_postfix + '(\d+)', file)
            if len(found) == 1:
                v = int(found[0])
                if v > highest_version:
                    highest_version = v

        new_version = filename + addon_prefs.backup_postfix + str(highest_version + 1) + ".blend"
        new_path = bpy.path.abspath("//") + new_version
        bpy.ops.wm.save_as_mainfile(filepath=new_path, copy=True)
        self.report({'INFO'}, "Backup saved: %s" % new_version)
        return {"FINISHED"}

    # -------------------  Promote FUNCTIONS -------------------------


# craetes a backup copy of a saved filed with the scheme [filename]_v[x]
# where x is an incremented version number
class VIEW3D_OT_rowdy_promote(bpy.types.Operator):
    """Promote file to production folder and updates linked libraries"""
    bl_idname = "rowdy.promote"
    bl_label = "Promote to production folder"

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        path = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        is_edit_file = self.is_in_edit_folder(addon_prefs.edit_folder_name, Path(path), addon_prefs.search_depth)

        if not is_edit_file:
            self.report({'ERROR'}, "File needs to be in edit folder")
            return {"CANCELLED"}

        prod_path = self.find_production_folder(addon_prefs.prod_folder_name, Path(path), addon_prefs.search_depth)

        if not prod_path:
            self.report({'ERROR'}, "No production folder was found")
            return {"CANCELLED"}

        new_path = os.path.join(prod_path, filename)

        broken_links = self.check_linked_libraries(prod_path)
        if broken_links:
            self.report({'ERROR'}, "Missing linked libraries in production folder: " + ", ".join(broken_links))
            return {"CANCELLED"}

        original_links = self.update_linked_libraries(prod_path)

        bpy.ops.wm.save_as_mainfile(filepath=new_path, copy=True)

        for link in bpy.data.libraries:
            if link in original_links:
                link.filepath = original_links[link]

        self.report({'INFO'}, "File promoted to: %s" % (new_path))

        return {"FINISHED"}

        # looks for a "production" folder recursively

    def find_production_folder(self, prod_folder_name, path, depth):
        parent_path = path.parent
        depth -= 1

        prod_path = os.path.join(path, prod_folder_name)
        if os.path.exists(prod_path):
            return prod_path

        if depth > 0:
            return self.find_production_folder(prod_folder_name, parent_path, depth)

    # checks whether a path contains an edit folder recursively
    def is_in_edit_folder(self, edit_folder_name, path, depth):
        depth -= 1
        is_in_edit = os.path.basename(path) == edit_folder_name
        if is_in_edit:
            return True

        if depth > 0:
            return self.is_in_edit_folder(edit_folder_name, path.parent, depth)
        else:
            return False

    # check if all linked libraries exist in production folder   
    def check_linked_libraries(self, prod_path):
        broken_links = []
        for link in bpy.data.libraries:
            linked_file = (bpy.path.basename(link.filepath))
            new_link = os.path.join(prod_path, linked_file)
            if not os.path.isfile(new_link):
                broken_links.append(link.name_full)

        return broken_links

    # updates all linked libraries to their corresponding production equivalent   
    def update_linked_libraries(self, prod_path):
        original_links = {}
        for link in bpy.data.libraries:
            linked_file = (bpy.path.basename(link.filepath))
            new_link = os.path.join(prod_path, linked_file)
            original_links[link] = link.filepath
            link.filepath = bpy.path.relpath(new_link)

        return original_links


# -------------------  PREFERENCES -------------------------

class RowdyToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    prod_folder_name: StringProperty(
        name="Production folder name",
        default='assets',
    )

    edit_folder_name: StringProperty(
        name="Edit folder name",
        default='edit',
    )

    search_depth: IntProperty(
        name="Search Depth",
        default=3,
    )

    backup_postfix: StringProperty(
        name="Backup postfix",
        default='_b',
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="RowdyTools Promote preferences")
        layout.prop(self, "prod_folder_name")
        layout.prop(self, "edit_folder_name")

        layout.prop(self, "search_depth")
        layout.label(text="RowdyTools Backup preferences")
        layout.prop(self, "backup_postfix")


def register():
    # Panels
    bpy.utils.register_class(VIEW3D_PT_rowdy_assets)

    # Operators
    bpy.utils.register_class(VIEW3D_OT_rowdy_promote)
    bpy.utils.register_class(VIEW3D_OT_rowdy_backup)

    # Preferences
    bpy.utils.register_class(RowdyToolsPreferences)


def unregister():
    # Panels
    bpy.utils.unregister_class(VIEW3D_PT_rowdy_assets)

    # Operators
    bpy.utils.unregister_class(VIEW3D_OT_rowdy_promote)
    bpy.utils.unregister_class(VIEW3D_OT_rowdy_backup)

    # Preferences
    bpy.utils.unregister_class(RowdyToolsPreferences)


if __name__ == '__main__':
    register()
