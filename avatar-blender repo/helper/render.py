import os
import shutil

import asyncio
import aiofiles

import cv2
import numpy as np


class Render:
    def __init__(self):
        os.makedirs("results", exist_ok=True)

    async def render(self, body, color, obj, mtl, text, filepath, gender):
        body_obj = f"assets/body/{gender}/{body}.fbx"
        body_text = f"{filepath}/textures"

        os.makedirs(body_text, exist_ok=True)

        # files = [obj, mtl, text]
        files, _ = await asyncio.gather(
            self.__set_file(filepath, obj, mtl, text),
            self.__fix_body_texture(body_text, color)
        )

        # obj, mtl, text, b_obj, b_text, b_type, path
        os.system(
            f"blender --background --python helper/blender.py -- {files[0]} {files[1]} {files[2]} {body_obj} {body_text} {body} {filepath} {gender}"
        )

    async def __set_file(self, filepath, obj, mtl, text):
        face_obj = f"{filepath}/face_object.obj"
        face_mtl = f"{filepath}/face_material.mtl"
        face_texture = f"{filepath}/face_texture.jpg"

        async with aiofiles.open(face_obj, 'wb') as obj_file:
            while obj_content := await obj.read(1024):
                await obj_file.write(obj_content)

        async with aiofiles.open(face_texture, 'wb') as text_file:
            while txt_content := await text.read(1024):
                await text_file.write(txt_content)

        async with aiofiles.open(face_mtl, 'wb') as mtl_path:
            while txt_content := await mtl.read(1024):
                await mtl_path.write(txt_content)

        return [face_obj, face_mtl, face_texture]

    async def __fix_body_texture(self, filepath, color):
        color = color[0].strip('[]').split(' ')
        color = [float(x) for x in color]

        names = ['assets/textures/Arm.png',
                 'assets/textures/Body.png',
                 'assets/textures/Head.png',
                 'assets/textures/Leg.png']

        for name in names:
            image = cv2.imread(name)
            image = self.__fix_color(image, color)

            cv2.imwrite(os.path.join(filepath, name.split("/")[-1]), image)

        shutil.copy("assets/textures/Nails.png", os.path.join(filepath, 'Nails.png'))
        shutil.copy("assets/textures/Hair1.png", os.path.join(filepath, 'Hair1.png'))
        shutil.copy("assets/textures/Hair2.png", os.path.join(filepath, 'Hair2.png'))

    def __fix_color(self, image, color):
        bgr_color = np.asarray(color, dtype=np.float64)
        bgr_color /= 255.0

        img = (image.astype('float64') * bgr_color).astype('uint8')

        return img