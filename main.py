from fastapi import FastAPI
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

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
genai.configure(api_key="API_KEY")

class QueryRequest(BaseModel):
    video_id: str
    query: str
    language: str

def fetch_transcript(video_id, language='en'):
    cleaned_video_id = video_id.strip('!')  # Remove any '!' at the end of the ID

    try:
        transcript = YouTubeTranscriptApi.get_transcript(cleaned_video_id, languages=[language])
        transcript_text = ' '.join([t['text'] for t in transcript])
        return transcript_text
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def get_gemini_response(context, query):
    prompt = (
        f"Context: {context}\n\n"
        f"Query: {query}\n\n"
        f"Please provide a concise answer in 2-3 lines only."
    )
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

@app.get("/")
async def root():
    return {"message": "QueryTube backend is live!"}

@app.post("/get_answer")
async def get_answer(request: QueryRequest):
    transcript_text = fetch_transcript(request.video_id, request.language)
    if transcript_text:
        answer = get_gemini_response(transcript_text, request.query)
        return {"answer": answer}
    return {"answer": "Failed to fetch transcript."}
