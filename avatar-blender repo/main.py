import os
import uuid
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Form, UploadFile, File
from starlette.responses import FileResponse

from helper import render
from helper.config import APP_HOST, APP_PORT, APP_STATE

app = FastAPI()


@app.get("/")
async def check_health():
    return "Healthy"


@app.post("/api/v1/create")
async def create(
        body_type: Annotated[str, Form()],
        body_color: Annotated[list, Form()],
        face_obj: UploadFile = File(...),
        face_material: UploadFile = File(...),
        face_texture: UploadFile = File(...),
        gender: Annotated[str, Form()] = " "
):
    filename = str(uuid.uuid4())
    filepath = f"results/{filename}"

    os.makedirs(filepath, exist_ok=True)

    await render.render(body_type, body_color, face_obj, face_material, face_texture, filepath, gender)

    return FileResponse(filepath + "/object.glb")

if __name__ == '__main__':
    uvicorn.run("main:app", host=APP_HOST, port=int(APP_PORT), reload=APP_STATE)
