from fastapi import FastAPI
import os

app = FastAPI()

print('env var', os.getenv('CLIENT_ID'))

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
