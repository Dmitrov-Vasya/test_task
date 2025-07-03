import os
from fastapi import FastAPI, UploadFile, HTTPException
import httpx
from PIL import Image
import io
from pydantic import BaseModel


app = FastAPI()


class ServerResponse(BaseModel):
    status: str
    reason: str | None = None


@app.post("/moderate", response_model=ServerResponse)
async def check_image_for_server(file: UploadFile):
    try:
        api_secret_key = "qKNzRZi9YBS27TDUsCbwPmHLe5S3bC83"
        api_user = "1576765018"
        if not api_secret_key:
            raise HTTPException(status_code=500, detail="API ключ не задан")
        else:
            print(f"Используем API ключ: {api_secret_key}")

        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_bytes_io = io.BytesIO()
        image.save(image_bytes_io, format='JPEG')
        image_bytes = image_bytes_io.getvalue()

        url = "https://api.sightengine.com/1.0/check.json"
        params = {
            'models': 'nudity',
            'api_user': api_user,
            'api_secret': api_secret_key,
        }

        files = {
            'media': ('image.jpg', image_bytes, 'image/jpeg'),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params, files=files)

        response.raise_for_status()
        data = response.json()

        nudity = data.get('nudity')
        if not nudity:
            raise HTTPException(
                status_code=500,
                detail="Ошибка получения данных от Sightengine.",
            )

        nudity_score = max(nudity.get('raw', 0), nudity.get('partial', 0), nudity.get('safe', 1))
        if nudity_score > 0.5:
            return {"status": "REJECTED", "reason": "NSFW content detected"}
        else:
            return {"status": "OK"}

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка запроса: {e}. Проверьте подключение к интернету."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))