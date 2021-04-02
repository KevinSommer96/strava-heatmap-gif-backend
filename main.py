from fastapi import FastAPI
import os
import requests
from fastapi.responses import RedirectResponse, FileResponse
from stravalib.client import Client
from fastapi.middleware.cors import CORSMiddleware
from pandas import json_normalize
import glob 
from PIL import Image, ImageColor
import polyline
import matplotlib.pyplot as plt
import base64
import shutil
import io
import cartopy.crs as ccrs
from cartopy.io.img_tiles import GoogleTiles, OSM

app = FastAPI()
client = Client()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://kevinsommer.com/",
    "https://kevinsommer.com",
    "http://www.kevinsommer.com",
    "https://www.kevinsommer.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper Functions 
def fig2img(fig): 
    buf = io.BytesIO()
    fig.savefig(buf, bbox_inches='tight', pad_inches=0, format='png')
    buf.seek(0)
    return Image.open(buf)

# Environment Variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URL = os.getenv('REDIRECT_URL')

@app.get("/")
def read_root():
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    return {"url": authorize_url}


@app.get("/authorised/")
def get_code(code=None):
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    access_token = token_response['access_token']
    refresh_token = token_response['refresh_token']
    expires_at = token_response['expires_at']

    return {"access_token": access_token, "refresh_token": refresh_token, "expires_at": expires_at }


@app.get('/gif/')
def get_gif(access_token: str, min_lon: float, max_lat: float, max_lon: float, min_lat: float, 
    ratio: float, colour: str, backgroundColour: str, alpha: float, activity_type: str, 
    bg_img: str, duration: int): 
    activities = requests.get('https://www.strava.com/api/v3/activities' + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(1))
    activities = activities.json()


    # convert activities to pandas dataframe
    df = json_normalize(activities)

    # filter df by type of activity
    if activity_type == 'Run':
        df = df[df['type'] == 'Run']
    elif activity_type == 'Ride': 
        df = df[df['type'] == 'Ride']
    else: 
        df = df[(df['type'] == 'Run') | (df['type'] == 'Ride')]

    # filter df by start coordinates using the bounding box
    df_bbox = df[(df['start_latitude'] < max_lat)  & (df['start_latitude'] > min_lat) & (df["start_longitude"] < max_lon) 
        & (df["start_longitude"] > min_lon)]

    df_bbox = df_bbox.sort_values(by=['start_date'])


    # create imagery based on bg_img
    if bg_img == 'sat':
        imagery = GoogleTiles(style='satellite')
    elif bg_img == 'osm':
        imagery = OSM()
    else: 
        imagery = OSM()

    # create figure to plot routes on
    fig = plt.figure(figsize=(8, ratio * 8), frameon=False)
    ax = fig.add_subplot(1, 1, 1, projection=imagery.crs)

    fig.patch.set_visible(False)
    ax.set_extent([min_lon, max_lon, min_lat, max_lat])
    
    ax.set_axis_off()

    # filepaths
    fp_out = 'image.gif'

    imgs = []
    for i in range(len(df_bbox)):
        try:
            lat, lng = zip(*polyline.decode(df_bbox.iloc[i]['map.summary_polyline']))
        except: 
            print(i)

        plt.plot(lng, lat, transform=ccrs.Geodetic(), color=colour, alpha=alpha)
        imgs.append(fig2img(fig))

    
    # create background image
    if bg_img == 'none':
        bg = Image.new(mode='RGBA', size=imgs[0].size, color=ImageColor.getrgb(backgroundColour))

    else:
        fig = plt.figure(figsize=(8, ratio * 8), frameon=False)
        ax = fig.add_subplot(1, 1, 1, projection=imagery.crs)
        ax.set_extent([min_lon, max_lon, min_lat, max_lat])
        fig.patch.set_visible(False)
        ax.set_axis_off()

        # set background imagery if one was sent
        ax.add_image(imagery, 15)

        # converting background to image
        bg = fig2img(fig)

    imgs = map(lambda img: Image.alpha_composite(bg, img), imgs)
    bg.save(fp=fp_out, format='GIF', append_images=imgs, save_all=True, duration=duration, loop=0)

    file = open('image.gif', 'rb')
    return {'gif': base64.b64encode(file.read())}
