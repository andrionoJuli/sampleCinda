import io
import os
import zipfile
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from starlette.responses import StreamingResponse, FileResponse

from helper import face_model
from helper.config import APP_HOST, APP_PORT, APP_STATE

app = FastAPI()


@app.get("/")
async def check_health():
    return "Healthy"


@app.post("/api/v1/face")
async def get_face(fixed: Annotated[bool, Form()] = True, face: UploadFile = File(...)):
    result, _ = await face_model.create_face(face, fixed)

    zip_bytes_io = io.BytesIO()
    with zipfile.ZipFile(zip_bytes_io, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for dirname, subdirs, files in os.walk(result):
            zipped.write(dirname)
            for filename in files:
                zipped.write(os.path.join(dirname, filename))

    response = StreamingResponse(
        iter([zip_bytes_io.getvalue()]),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment;filename=output.zip",
                 "Content-Length": str(zip_bytes_io.getbuffer().nbytes)}
    )
    zip_bytes_io.close()

    return response


@app.post("/api/v1/avatar")
async def get_face(body: Annotated[str, Form()], gender: Annotated[str, Form()], face: UploadFile = File(...)):
    result = await face_model.create_avatar(face, body, gender)

    return FileResponse(result)


if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=int(APP_PORT), reload=APP_STATE)