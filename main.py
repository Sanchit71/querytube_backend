from fastapi import FastAPI
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import re
import traceback

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust according to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the Gemini API key
genai.configure(api_key="AIzaSyB77OH3ryUNZBOGgvCYR8JGD4w6H7XvRtU")  # Replace with your actual key

# Define the request schema
class QueryRequest(BaseModel):
    video_id: str
    query: str
    language: str

# Fetch transcript from YouTube
def fetch_transcript(video_id, language='en'):
    # Clean the video_id to ensure no unwanted characters
    cleaned_video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
    print(f"Fetching transcript for video_id: {cleaned_video_id}, language: {language}")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(cleaned_video_id, languages=[language])
        transcript_text = ' '.join([t['text'] for t in transcript])
        print("Transcript fetched successfully.")
        return transcript_text
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
    print("Received request:", request.dict())  # Debug incoming request

    transcript_text = fetch_transcript(request.video_id, request.language)
    if transcript_text:
        answer = get_gemini_response(transcript_text, request.query)
        return {"answer": answer}
    return {"answer": "Failed to fetch transcript. Make sure the video has captions and the video_id is valid."}
