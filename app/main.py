from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import re
from bs4 import BeautifulSoup

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoTitle(BaseModel):
    url: str
    platform: str

@app.post("/get-video-title")
async def get_video_title(video: VideoTitle):
    async with httpx.AsyncClient() as client:
        try:
            if video.platform == "youtube":
                # Extract video ID from various YouTube URL formats
                video_id = None
                clean_url = video.url.strip()

                # youtu.be format
                if 'youtu.be/' in clean_url:
                    video_id = clean_url.split('youtu.be/')[-1]
                # youtube.com/v/ format
                elif '/v/' in clean_url:
                    video_id = clean_url.split('/v/')[-1]
                # watch?v= format
                elif 'watch?v=' in clean_url:
                    video_id = clean_url.split('watch?v=')[-1]
                # embed format
                elif 'embed/' in clean_url:
                    video_id = clean_url.split('embed/')[-1]

                # Clean up video ID
                if video_id:
                    video_id = video_id.split('&')[0].split('?')[0].split('#')[0]

                if not video_id:
                    raise HTTPException(status_code=400, detail="Invalid YouTube URL")

                # Try multiple services to get video info
                services = [
                    f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}",
                    f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                ]

                title = None
                for oembed_url in services:
                    print(f"Trying service: {oembed_url}")  # Debug log
                    try:
                        response = await client.get(oembed_url, headers={
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                            'Accept': 'application/json'
                        }, timeout=5.0)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('title'):
                                title = data['title']
                                break
                    except Exception as e:
                        print(f"Service error: {str(e)}")  # Debug log
                        continue

                if title:
                    return {"title": title}
                
                raise HTTPException(status_code=400, detail="无法获取YouTube视频标题，请检查链接是否正确")

            elif video.platform == "bilibili":
                # Extract BV ID
                # Handle bilibili URLs
                bv_id = re.search(r'video/(BV[A-Za-z0-9]+)', video.url)
                if not bv_id:
                    raise HTTPException(status_code=400, detail="Invalid Bilibili URL")
                
                # Fetch video page
                headers = {'User-Agent': 'Mozilla/5.0'}
                # Fetch video page with proper headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://www.bilibili.com/'
                }
                url = f"https://www.bilibili.com/video/{bv_id.group(1)}"
                print(f"Fetching bilibili video: {url}")  # Debug log
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Could not fetch Bilibili video")
                
                # Parse title
                soup = BeautifulSoup(response.text, 'html.parser')
                # Try different methods to get the title
                title = None
                # Try meta tag first
                meta_title = soup.find('meta', {'property': 'og:title'})
                if meta_title and meta_title.get('content'):
                    title = meta_title.get('content')
                
                # Try h1 tag if meta tag failed
                if not title:
                    h1_title = soup.find('h1')
                    if h1_title:
                        title = h1_title.get_text(strip=True)

                # Try title tag if both failed
                if not title:
                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.get_text(strip=True).replace('_哔哩哔哩_bilibili', '').strip()

                if title:
                    return {"title": title}

        except Exception as e:
            print(f"Error processing video: {str(e)}")  # Debug log
            raise HTTPException(status_code=500, detail=str(e))
    
    print(f"Could not extract title for URL: {video.url}")  # Debug log
    raise HTTPException(status_code=400, detail="Could not extract video title")


# In-memory storage
videos_db = []

class Video(BaseModel):
    id: str
    url: str
    title: str
    platform: str  # "youtube" or "bilibili"
    thumbnail: Optional[str] = None
    thumbnailColor: Optional[str] = None

@app.get("/videos", response_model=List[Video])
async def get_videos():
    return videos_db

@app.post("/videos")
async def add_video(video: Video):
    print(f"Received video: {video.dict()}")  # Debug log
    try:
        video_data = video.dict()
        videos_db.append(video_data)
        print(f"Added video successfully. DB now has {len(videos_db)} videos")  # Debug log
        return {"message": "Video added successfully"}
    except Exception as e:
        print(f"Error adding video: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
