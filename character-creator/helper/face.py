import asyncio
import gc
import math
import os
import uuid

import cv2
import requests
import torch
import numpy as np

from fastapi import UploadFile, HTTPException

from models.hrn import Reconstructor

from helper.config import BLENDER_HOST, BLENDER_PORT


class Face:
    def __init__(self):
        self.model = Reconstructor(
            params=[
                "--checkpoints_dir",
                "assets/pretrained_models",
                "--name",
                "hrn_v1.1",
                "--epoch",
                "10",
            ]
        )

        os.makedirs("results", exist_ok=True)
        self.save_path = "results"

    async def create_face(self, image, fixed=True):
        filename = str(uuid.uuid4())
        filepath = f"{self.save_path}/{filename}"

        os.makedirs(filepath, exist_ok=True)

        face = await self.__read_image(image)

        await asyncio.create_task(
            self.model.predict(
                face,
                visualize=True,
                save_name=filename,
                out_dir=filepath
            ))

        face_text_path = f"{filepath}/face_texture.jpg"
        hi_face_text_path = f"{filepath}/hi_face_texture.jpg"

        color = 0
        if fixed:
            color = await self.__extract_color(face_text_path)

            await self.__fix_face(face_text_path, hi_face_text_path, color)

        gc.collect()
        torch.cuda.empty_cache()

        return filepath, color

    # Combine the process in one image instead not use URL to access the blender
    async def create_avatar(self, image, body, gender):
        filepath, color = await asyncio.create_task(
            self.create_face(
                image
            )
        )

        face_obj = f"{filepath}/face_object.obj"
        face_mtl = f"{filepath}/face_material.mtl"
        face_texture = f"{filepath}/face_texture.jpg"

        return await self.__render(
            body,
            color,
            face_obj,
            face_mtl,
            face_texture,
            filepath,
            gender
        )

    async def __render(self, body, color, obj, mtl, text, path, gender):
        url = f"http://{BLENDER_HOST}:{BLENDER_PORT}/api/v1/create"

        files = {
            "body_type": (None, body),
            "body_color": (None, str(color)),
            "face_obj": ("_0_hrn_high_mesh.obj", open(obj, 'rb')),
            "face_material": ("_0_hrn_mid_mesh.mtl", open(mtl, 'rb')),
            "face_texture": ("_0_hrn_mid_mesh.jpg", open(text, 'rb')),
            "gender": (None, gender)
        }

        response = requests.post(url, files=files)
        try:
            result_path = f"{path}/object.glb"
            if response.ok:
                with open(result_path, "wb") as f:
                    f.write(response.content)
                    f.close()
            if not os.path.exists(result_path):
                raise FileNotFoundError(f"No such file or directory: '{result_path}'")
            return result_path
        except FileNotFoundError as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def __fix_face(self, face_text_path, hi_face_text_path, color, lighten=1):
        mask = cv2.imread("assets/mask/face.png")
        texture = cv2.imread(face_text_path)
        hi_texture = cv2.imread(hi_face_text_path)

        for row in range(0, texture.shape[0]):  # 256 * 256
            for col in range(0, texture.shape[1]):

                x = col - 128
                y = -(row - 128)

                calculation = (y ** 2) + ((x ** 2) / .5906) * (2.71828 ** (.1 * y * math.log(.95)))
                if calculation > 10000:
                    texture[row][col] = color
                elif calculation > 7000:
                    texture[row][col] = self.__lerp_color(
                        [np.clip(round(x * lighten), 0, 255) for x in texture[row][col]], color,
                        (calculation - 7000) / 3000)
                else:
                    texture[row][col] = [np.clip(round(x * lighten), 0, 255) for x in texture[row][col]]

                if mask[row][col][0] > 0:
                    texture[row][col] = self.__lerp_color(texture[row][col], hi_texture[row][col],
                                                          mask[row][col][0] / 255)
        cv2.imwrite(face_text_path, texture)

    async def __extract_color(self, image):
        image = cv2.imread(image)
        x, y = [35, 128]

        roi = image[
              x - 5: x + 5, y - 5: y + 5
              ]  # Customize the ROI size here (50x50 pixels)
        color_rgb = np.mean(roi, axis=(0, 1)).astype(int)

        return color_rgb

    async def __read_image(self, image: UploadFile):
        img = await image.read()
        img = np.fromstring(img, np.uint8)

        return cv2.imdecode(img, cv2.IMREAD_COLOR)

    def __lerp(self, a, b, t):
        return math.sqrt(a ** 2 + (b ** 2 - a ** 2) * t)

    def __lerp_color(self, a, b, t):
        return self.__lerp(a[0], b[0], t), self.__lerp(a[1], b[1], t), self.__lerp(a[2], b[2], t)