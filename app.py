from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mylogic import process_video_from_youtube

app = FastAPI()

# Define the input schema
class YouTubeURL(BaseModel):
    url: str

# Define the API route
@app.post("/process")
def process_youtube_video(data: YouTubeURL):
    try:
        # Call the logic function with the provided URL
        result = process_video_from_youtube(data.url)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))