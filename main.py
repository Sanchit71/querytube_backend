from fastapi import FastAPI
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import re
import traceback
import os
import time
from requests.exceptions import ChunkedEncodingError, ConnectionError

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define the request schema
class QueryRequest(BaseModel):
    video_id: str
    query: str
    language: str

# Fetch transcript from YouTube
def fetch_transcript(video_id, language='en', max_retries=3):
    cleaned_video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
    print(f"Fetching transcript for video_id: {cleaned_video_id}, language: {language}")

    for attempt in range(max_retries):
        try:
            # Try without proxy first
            if attempt == 0:
                transcript_api = YouTubeTranscriptApi()
            else:
                # Set up proxy configuration for retry attempts
                proxy_config = GenericProxyConfig(
                    http_url="http://117.250.3.58:8080",
                    https_url="http://117.250.3.58:8080"
                )
                transcript_api = YouTubeTranscriptApi(proxy_config=proxy_config)
            
            # Fetch transcript
            transcript = transcript_api.fetch(cleaned_video_id, languages=[language])
            transcript_text = ' '.join([t.text for t in transcript])
            print("Transcript fetched successfully.")
            return transcript_text
            
        except (ChunkedEncodingError, ConnectionError) as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"All {max_retries} attempts failed")
                traceback.print_exc()
                return None
        except Exception as e:
            print(f"Error fetching transcript for video ID {cleaned_video_id}: {e}")
            traceback.print_exc()
            return None

# Generate a Gemini response
def get_gemini_response(context, query):
    prompt = (
        f"Context: {context}\n\n"
        f"Query: {query}\n\n"
        f"Please provide a concise answer in 2-3 lines only."
    )
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

# Health check route
@app.get("/")
async def root():
    return {"message": "QueryTube backend is live!"}

# Main endpoint to handle query
@app.post("/get_answer")
async def get_answer(request: QueryRequest):
    print("Received request:", request.dict())

    transcript_text = fetch_transcript(request.video_id, request.language)
    if transcript_text:
        answer = get_gemini_response(transcript_text, request.query)
        return {
            "answer": answer,
            "video_id": request.video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={request.video_id}"
        }

    return {
        "answer": "Failed to fetch transcript. Make sure the video has captions and the video_id is valid.",
        "video_id": request.video_id,
        "youtube_url": f"https://www.youtube.com/watch?v={request.video_id}"
    }

# Only used if you run `python main.py` locally
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
