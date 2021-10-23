"""
We are create a microserver that would take off load from our main app.
This microservice can be used any apps in the future that require this functionality

app
- init
- main

The flask development server is not suited for produtction its not able to take in multiple requires and not good for scailbilty
Something like WSGI server: gunicorn fixes this and makes it much more suitable for production enivornment

path to our api is app.main:app
we will use univorn to grab that: uvicorn app.main:app --reload

REST API:  app to app communication.

FASTAPI makes every endpoint by default return json (unless you change it) so we dont have to do json.dumps

Flush out testing before going to production to make sure we dont have any bugs at production

In digital ocean we will make the run command: gunicorn --worker-tmp-dir /dev/shm -k uvicorn.workers.UvicornWorker app.main:app

Downside to deploy like this (without docker and stuff) is lack of control the actual os environments. So what we are gonna do now is
deploy docker file to handle this.

Now we have two different environments. One in product (digitalocean) and one in development local. Now we will add debug which tells us which environment we are in

"""

import os
import io
import pathlib
import uuid
from PIL import Image
from fastapi import FastAPI, Request, Depends, File, UploadFile, HTTPException
from fastapi import templating
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    debug: bool
    echo_active: bool = False
    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
DEBUG = settings.debug


BASE_DIR = "app"
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse) # http GET -> JSON
def home_view(request: Request, settings:Settings = Depends(get_settings)):
    #print(request)

    print(settings.debug)
    return templates.TemplateResponse("home.html", {"request": request, "test_arg": 123})


@app.post("/") # http POST -> JSON
def home_detail_view():
    return {"hello": "world"}

# when ever we are uploading files we need to use async view thats why we use uvicorn too
@app.post("/image-echo/", response_class=FileResponse)
async def image_echo_view(file:UploadFile = File(...), settings:Settings = Depends(get_settings)):
    
    # when we go to production we will have lack of response
    if not settings.echo_active:
        raise HTTPException(detail="Invalid endpoint", status_code=400)

    # creates the upload directory for images if it doesnt already exists
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    bytes = await file.read()
    bytes_str = io.BytesIO(bytes)

    # can also use opencv instead of PIL here
    try:
        image = Image.open(bytes_str)
    except:
        raise HTTPException(detail="Invalid image", status_code=400)

    # uuid helps us handle the case where we upload image with same name again
    fext = file.filename.split(".")[-1]
    fdest = os.path.join(UPLOAD_DIR, f"{uuid.uuid1()}.{fext}")

    image.save(fdest)

    return fdest