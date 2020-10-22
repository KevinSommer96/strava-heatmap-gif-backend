from fastapi import FastAPI
import os
import requests
from fastapi.responses import RedirectResponse, FileResponse
from stravalib.client import Client
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
client = Client()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000"
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

@app.get("/gif")
def get_gif(access_token: str): 
    return {'test': 'ok'}