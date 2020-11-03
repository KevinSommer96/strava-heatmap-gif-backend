from fastapi import FastAPI
import os
import requests
from fastapi.responses import RedirectResponse, FileResponse
from stravalib.client import Client
from fastapi.middleware.cors import CORSMiddleware
from pandas import json_normalize
import glob 
from PIL import Image
import polyline
import matplotlib.pyplot as plt
import base64
import math
import shutil

app = FastAPI()
client = Client()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://kevinsommer.com",
    "https://kevinsommer.com",
    "http://www.kevinsommer.com",
    "https://www.kevinsommer.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Environment Variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URL = os.getenv('REDIRECT_URL')

@app.get("/")
def read_root():
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    print(authorize_url)
    return {"url": authorize_url}
    # return RedirectResponse(authorize_url)


@app.get("/authorised/")
def get_code(code=None):
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    access_token = token_response['access_token']
    refresh_token = token_response['refresh_token']
    expires_at = token_response['expires_at']

    return {"access_token": access_token, "refresh_token": refresh_token, "expires_at": expires_at }

@app.get("/activities/")
def get_activities(access_token: str):
    
    r = requests.get('https://www.strava.com/api/v3/activities' + '?access_token=' + access_token)
    r = r.json()
    
    return {'activities': r}

@app.get('/gif/')
def get_gif(access_token: str, min_lon: float, max_lat: float, max_lon: float, min_lat: float, 
    ratio: float, colour: str, backgroundColour: str, alpha: float): 
    activities = requests.get('https://www.strava.com/api/v3/activities' + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(1))
    activities = activities.json()


    df = json_normalize(activities)
    df = df[df['type'] == 'Run']

    df_ac = df[(df['start_latitude'] < max_lat)  & (df['start_latitude'] > min_lat) & (df["start_longitude"] < max_lon) 
        & (df["start_longitude"] > min_lon)]

    df_ac = df_ac.sort_values(by=['start_date'])

    fig = plt.figure(figsize=(8, ratio * 8))

    fig.patch.set_facecolor(backgroundColour)
    plt.xlim(min_lon, max_lon)
    plt.ylim(min_lat, max_lat)
    plt.xticks()
    plt.yticks()
    plt.axis('off')

    # filepaths
    fp_in = './images/*.png'
    fp_out = 'image.gif'

    shutil.rmtree('./images')
    os.mkdir('images')

    for i in range(len(df_ac)):
        try:
            latitude, longitude = zip(*polyline.decode(df_ac.iloc[i]['map.summary_polyline']))
        except: 
            print(i)
        plt.plot(longitude, latitude, color=colour, alpha=alpha)
        plt.savefig('./images/strava_plot_' + '_' + str(i).zfill(4) + '.png', bbox_inches='tight')



    img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
    img.save(fp=fp_out, format='GIF', append_images=imgs, save_all=True, duration=200, loop=0)

    file = open('image.gif', 'rb')
    return {'gif': base64.b64encode(file.read())}
