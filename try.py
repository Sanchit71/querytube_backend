import requests

url = "https://querytube-backend.onrender.com/get_answer"
payload = {
    "video_id": "sTyPSKqSwwk",  # Only the video ID, not the full URL
    "query": "What is this video about?",
    "language": "english"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
