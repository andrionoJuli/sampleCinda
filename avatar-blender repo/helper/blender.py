import bpy
import bmesh
import mathutils

import os
import sys
import json


# KERIS

class Blender:
    def get_args(self):
        argv = sys.argv
        argv = argv[argv.index("--") + 1:]

        bpy.ops.wm.read_homefile(use_empty=True)

        return argv

    def get_params(self, body, gender):
        if gender == "female":
            with open('assets/json/f_params.json') as json_file:
                data = json.load(json_file)
                json_file.close()
        else:
            with open('assets/json/m_params.json') as json_file:
                data = json.load(json_file)
                json_file.close()

        return data[body]

    def remove_values_recursive(self, original_list, remove_list):
        if len(original_list) == 0:
            return []
        else:
            if original_list[0] in remove_list:
                return self.remove_values_recursive(original_list[1:], remove_list)
            else:
                return [original_list[0]] + self.remove_values_recursive(original_list[1:], remove_list)

    def import_obj(self, path):
        bpy.ops.wm.obj_import(filepath=path)

    def import_fbx(self, path):
        bpy.ops.import_scene.fbx(filepath=path)

    def export_glb(self, path, gender):
        if gender == "female":
            bpy.ops.file.pack_all()

        bpy.ops.export_scene.gltf(filepath=path)

    def save_blend(self, path):
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_mainfile(filepath=path)

    def import_blend(self, path):
        bpy.ops.wm.open_mainfile(filepath=path)

    def import_obj_return(self, path):
        old_objs = []
        for obj in bpy.data.objects:
            old_objs.append(obj)

        self.import_obj(path)

        return self.remove_values_recursive(bpy.data.objects, old_objs)

    def add_texture_to_face(self, face, texture_path):
        new_mat = bpy.data.materials.new(name="new_face")

        img = bpy.data.images.load(texture_path)

        new_mat.use_nodes = True

        # material_output = new_mat.node_tree.nodes.get('Material Output')
        principled_BSDF = new_mat.node_tree.nodes.get('Principled BSDF')

        tex_node = new_mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_node.image = img

        new_mat.node_tree.links.new(tex_node.outputs[0], principled_BSDF.inputs[0])
        face.data.materials.append(new_mat)

    def prep_face_to_edit(self):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.data.objects[0].select_set(False)
        bpy.ops.object.transform_apply()
        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.object.vertex_group_add()
        bpy.context.active_object.vertex_groups.active.name = "CC_Base_Head"
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.14159, shape_threshold=3.14159, uvs=False, vcols=False,
                                           seam=False, sharp=False, materials=False)
        bpy.ops.mesh.region_to_loop()

    def edit_face_transform(self, dimension):
        face_width = dimension[0]
        y_val = dimension[1]
        z_val = dimension[2]

        bm_face = bmesh.from_edit_mesh(bpy.context.active_object.data)
        bm_face.verts.ensure_lookup_table()

        selected_verts_face = [v for v in bm_face.verts if v.select]

        x_plus = selected_verts_face[0]
        x_minus = selected_verts_face[0]
        y_minus = selected_verts_face[0]
        z_plus = selected_verts_face[0]
        z_minus = selected_verts_face[0]

        for vert in selected_verts_face:
            if vert.co.y > y_minus.co.y:
                y_minus = vert
            if vert.co.y > x_plus.co.y and vert.co.x > 0.25:
                x_plus = vert
            if vert.co.y > x_minus.co.y and vert.co.x < -0.25:
                x_minus = vert
            if vert.co.z > z_plus.co.z and vert.co.x < 0.05 and vert.co.x > -0.05:
                z_plus = vert
            if vert.co.z < z_minus.co.z and vert.co.x < 0.05 and vert.co.x > -0.05:
                z_minus = vert

        x_line = x_plus.co - x_minus.co
        x_line.z = 0
        x_line_2d = mathutils.Vector((x_line.x, x_line.y))
        z_angle = x_line_2d.angle_signed(mathutils.Vector((1, 0)), 0)

        z_line = z_plus.co - z_minus.co
        z_line.x = 0
        z_line_2d = mathutils.Vector((z_line.z, z_line.y))
        x_angle = -z_line_2d.angle_signed(mathutils.Vector((1, -0.05)))

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.rotate(value=z_angle)
        bpy.ops.transform.rotate(value=x_angle, orient_axis='X')
        bpy.ops.mesh.region_to_loop()

        selected_verts_face = [v for v in bm_face.verts if v.select]

        x_plus = selected_verts_face[0]
        x_minus = selected_verts_face[0]
        y_minus = selected_verts_face[0]
        z_plus = selected_verts_face[0]
        z_minus = selected_verts_face[0]
        for vert in selected_verts_face:
            if vert.co.y > y_minus.co.y:
                y_minus = vert
            if vert.co.y > x_plus.co.y and vert.co.x > 0.25:
                x_plus = vert
            if vert.co.y > x_minus.co.y and vert.co.x < -0.25:
                x_minus = vert
            if vert.co.z > z_plus.co.z and vert.co.x < 0.05 and vert.co.x > -0.05:
                z_plus = vert
            if vert.co.z < z_minus.co.z and vert.co.x < 0.05 and vert.co.x > -0.05:
                z_minus = vert

        bpy.ops.mesh.select_all(action='SELECT')
        x_line = x_plus.co - x_minus.co
        scale = face_width / x_line.x
        bpy.ops.transform.resize(value=(scale, scale, scale))

        translate = -(x_plus.co + x_minus.co) / 2
        translate.y = y_val - x_plus.co.y
        translate.z = z_val - z_minus.co.z

        bpy.ops.transform.translate(value=translate)

        bpy.ops.mesh.select_all(action='DESELECT')
        x_plus.select_set(True)
        x_minus.select_set(True)
        # y_minus.select_set(True)
        z_plus.select_set(True)
        z_minus.select_set(True)

        bmesh.update_edit_mesh(bpy.context.object.data)

    def attach_face_to_body(self, face_loop_length):
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = bpy.data.objects[0]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[0]
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.14159, shape_threshold=3.14159, uvs=False, vcols=False,
                                           seam=False, sharp=False, materials=False)
        bpy.ops.mesh.region_to_loop()

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bpy.context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        selected_verts = [v for v in bm.verts if v.select]

        i = 0
        list_of_loops = []
        body_loop = []
        face_loop = []
        while len(selected_verts) > 0:
            if i == 2000:
                break
            new_loop = []
            new_loop.append(selected_verts[0])
            window = []
            window.append(selected_verts[0])
            root_link = selected_verts[0]
            prev_link = root_link
            curr_link = root_link
            selected_verts.pop(0)

            while True:
                i = i + 1
                if i == 2000:
                    break
                vl = []
                for l in curr_link.link_edges:
                    vl.append(l.other_vert(curr_link))

                connected_verts = list(filter(lambda c_v: c_v.select, vl))
                connected_verts = list(filter(lambda c_v: c_v in selected_verts, connected_verts))
                if len(connected_verts) <= 0:
                    break
                else:
                    vl_indices = []
                    for vert in connected_verts:
                        vl_indices.append(vert.index)
                    if prev_link in connected_verts:
                        connected_verts.remove(prev_link)

                    prev_link = curr_link
                    curr_link = connected_verts[0]
                    if curr_link == root_link:
                        break
                    if curr_link in selected_verts:
                        selected_verts.remove(curr_link)
                    else:
                        print("Current link is not in selected link list. Something is wrong")

                    new_loop.append(curr_link)

                    window.append(curr_link)
                    window_length = len(window)

                    if window_length == 3:
                        window[1].co.x = (window[0].co.x + window[2].co.x) / 2
                        window[1].co.y = (window[0].co.y + window[2].co.y) / 2
                        window[1].co.z = (window[0].co.z + window[2].co.z) / 2
                    elif window_length == 5:
                        window[2].co.x = (window[0].co.x + window[1].co.x + window[3].co.x + window[4].co.x) / 4
                        window[2].co.y = (window[0].co.y + window[1].co.y + window[3].co.y + window[4].co.y) / 4
                        window[2].co.z = (window[0].co.z + window[1].co.z + window[3].co.z + window[4].co.z) / 4
                    elif window_length == 6:
                        window.pop(0)
                        window[2].co.x = (window[0].co.x + window[1].co.x + window[3].co.x + window[4].co.x) / 4
                        window[2].co.y = (window[0].co.y + window[1].co.y + window[3].co.y + window[4].co.y) / 4
                        window[2].co.z = (window[0].co.z + window[1].co.z + window[3].co.z + window[4].co.z) / 4
                    elif window_length > 6:
                        print("Window length is more than 6, something is wrong.")

            list_of_loops.append(new_loop)

            if len(new_loop) == face_loop_length:
                body_loop = new_loop

        if body_loop in list_of_loops:
            list_of_loops.remove(body_loop)
        length = 0
        for loop in list_of_loops:
            if length < len(loop):
                face_loop = loop
                length = len(loop)
        if face_loop in list_of_loops:
            list_of_loops.remove(face_loop)
        for loop in list_of_loops:
            for vert in loop:
                vert.select_set(False)

        # creating kd tree
        kd = mathutils.kdtree.KDTree(len(body_loop))
        for vert in body_loop:
            coord = vert.co.copy()
            coord.y = 0
            kd.insert(coord, vert.index)
        kd.balance()

        for vert in face_loop:
            new_edge_verts = []
            new_edge_verts.append(vert)
            vert_coord = vert.co.copy()
            vert_coord.y = 0
            co, index, dist = kd.find(vert_coord)
            vert2 = list(filter(lambda x: x.index == index, body_loop))
            if len(vert2) > 0:
                # print("creating new edge")
                new_edge_verts.append(vert2[0])
                bm.edges.new(new_edge_verts)

        # last smoothing
        body2_loop = []
        body3_loop = []
        for vert in body_loop:
            vert_co = mathutils.Vector((0.0, 0.0, 0.0))
            link_len = 0
            for l in vert.link_edges:
                other_vert = l.other_vert(vert)
                vert_co = vert_co + other_vert.co
                link_len = link_len + 1
                if not other_vert.select and not (other_vert in body2_loop):
                    body2_loop.append(other_vert)
            if link_len > 0:
                vert.co = vert_co / link_len
        for vert in body2_loop:
            vert_co = vert.co / 4
            link_len = 0.25
            for l in vert.link_edges:
                other_vert = l.other_vert(vert)
                vert_co = vert_co + other_vert.co
                link_len = link_len + 1
                if not (other_vert in body_loop) and not (other_vert in body2_loop):
                    body3_loop.append(other_vert)
            if link_len > 0:
                vert.co = vert_co / link_len
        for vert in body3_loop:
            vert_co = vert.co / 2
            link_len = .5
            for l in vert.link_edges:
                vert_co = vert_co + l.other_vert(vert).co
                link_len = link_len + 1
            if link_len > 0:
                vert.co = vert_co / link_len
        for vert in face_loop:
            vert_co = mathutils.Vector((0.0, 0.0, 0.0))
            link_len = 0
            for l in vert.link_edges:
                vert_co = vert_co + l.other_vert(vert).co
                link_len = link_len + 1
            if link_len > 0:
                vert.co = vert_co / link_len
        for vert in face_loop:
            vert_co = mathutils.Vector((0.0, 0.0, 0.0))
            link_len = 0
            for l in vert.link_edges:
                if l.other_vert(vert) in face_loop:
                    vert_co = vert_co + l.other_vert(vert).co
                    link_len = link_len + 1
            if link_len > 0:
                vert.co = vert_co / link_len
        for vert in body_loop:
            vert_co = mathutils.Vector((0.0, 0.0, 0.0))
            link_len = 0
            for l in vert.link_edges:
                if l.other_vert(vert) in body_loop:
                    vert_co = vert_co + l.other_vert(vert).co
                    link_len = link_len + 1
            if link_len > 0:
                vert.co = vert_co / link_len
        for vert in body_loop:
            vert_co = mathutils.Vector((0.0, 0.0, 0.0))
            link_len = 0
            for l in vert.link_edges:
                if l.other_vert(vert) in body_loop:
                    vert_co = vert_co + l.other_vert(vert).co
                    link_len = link_len + 1
            if link_len > 0:
                vert.co = vert_co / link_len

        bmesh.update_edit_mesh(bpy.context.object.data)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edge_face_add()

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()

        bpy.ops.mesh.decimate(ratio=0.05)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth(use_auto_smooth=False, auto_smooth_angle=0.523599)

    def replace_image(self, slot, path):
        bpy.data.images[slot].filepath = path

    def replace_skin(self, path):
        bpy.ops.file.unpack_all(method='REMOVE')

        slot = ['Nails', 'Arm', 'Body', 'Head', 'Leg']

        for name in slot:
            slot_path = os.path.join(path, f"{name}.png")
            self.replace_image(f"{name}.jpg", slot_path)


if __name__ == "__main__":
    blender = Blender()

    # obj, mtl, text, b_obj, b_text, b_type, path, gender
    arg = blender.get_args()

    # b_obj
    blender.import_fbx(arg[3])

    # b_text
    if arg[7] == "female":
        blender.replace_skin(arg[4])

    # obj
    face = blender.import_obj_return(arg[0])

    # txt
    blender.add_texture_to_face(face[0], arg[2])

    blender.prep_face_to_edit()

    # b_type
    dimension = blender.get_params(arg[5], arg[7])
    blender.edit_face_transform(dimension)

    if arg[7] == "female":
        blender.attach_face_to_body(240)
    else:
        blender.attach_face_to_body(210)

    # path
    blender.export_glb(arg[6] + "/object", arg[7])