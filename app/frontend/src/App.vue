<template>
  <div class="app">
    <h1>My Favorite Videos</h1>
    
    <div class="add-video-container">
      <div class="add-video">
        <input 
          v-model="shareInput" 
          placeholder="粘贴分享链接 (支持 B站分享文本或 YouTube 链接)"
          style="flex-grow: 1;"
          @paste="handlePaste"
        >
        <button 
          @click="addVideo" 
          :disabled="!canAddVideo || isAddingVideo || isDuplicateVideo || videos.length >= 10"
          class="add-button"
          :class="{ 'loading': isAddingVideo }"
        >
          {{ isAddingVideo ? '添加中...' : '添加视频' }}
        </button>
      </div>
      <div v-if="error || isDuplicateVideo" class="error-message">
        {{ error || '该视频已存在' }}
      </div>
      <div v-if="isFetchingTitle" class="status-message">
        获取视频信息中...
      </div>
    </div>

    <div class="video-grid">
      <div v-for="video in sortedVideos" :key="video.id" class="video-card" @click="playVideo(video)">
        <div class="video-thumbnail-container">
          <template v-if="video.platform === 'bilibili'">
            <div class="video-thumbnail bilibili-thumbnail" :style="{ backgroundColor: video.thumbnailColor }"></div>
          </template>
          <template v-else>
            <img v-if="video.thumbnail" :src="video.thumbnail" :alt="video.title" class="video-thumbnail">
            <img v-else src="https://via.placeholder.com/300x200?text=Loading..." :alt="video.title" class="video-thumbnail">
          </template>
        </div>
        <div class="video-info">
          <h3>{{ video.title }}</h3>
          <p>{{ video.platform }}</p>
        </div>
        <button @click.stop="removeVideo(video)" class="remove-button">删除</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      videos: [],
      shareInput: '',
      newVideo: null,
      isFetchingTitle: false,
      isAddingVideo: false,
      error: null
    }
  },
  computed: {
    canAddVideo() {
      return this.newVideo && this.newVideo.url && this.newVideo.title && this.newVideo.platform && this.videos.length < 10;
    },
    sortedVideos() {
      return [...this.videos].sort((a, b) => parseInt(b.id) - parseInt(a.id));
    },
    isDuplicateVideo() {
      if (!this.newVideo) return false;
      try {
        const newVideoUrl = new URL(this.newVideo.url);
        const newVideoBaseUrl = `${newVideoUrl.origin}${newVideoUrl.pathname}`;
        return this.videos.some(v => {
          const existingVideoUrl = new URL(v.url);
          const existingVideoBaseUrl = `${existingVideoUrl.origin}${existingVideoUrl.pathname}`;
          return existingVideoBaseUrl === newVideoBaseUrl;
        });
      } catch (error) {
        console.error("Error parsing URL:", error);
        return false;
      }
    }
  },
  watch: {
    shareInput() {
      this.error = null;
    }
  },
  async created() {
    await this.fetchVideos();
  },
  methods: {
    async getVideoTitle(url, platform) {
      try {
        const response = await fetch('http://localhost:8000/get-video-title', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url, platform })
        });
        
        if (response.ok) {
          const data = await response.json();
          return data.title;
        } else {
          const error = await response.json();
          throw new Error(error.detail || '获取视频标题失败');
        }
      } catch (error) {
        console.error('Error fetching video title:', error);
        this.error = error.message || '获取视频标题失败，请检查链接是否正确';
        return '';
      }
    },
    async fetchVideos() {
      try {
        const response = await fetch('http://localhost:8000/videos');
        if (!response.ok) {
          throw new Error('Failed to fetch videos');
        }
        const videos = await response.json();
        
        this.videos = await Promise.all(videos.map(async video => {
          const { thumbnail, thumbnailColor } = await this.getThumbnail(video);
          return {
            ...video,
            thumbnail,
            thumbnailColor
          };
        }));
      } catch (error) {
        console.error('Error fetching videos:', error);
        this.error = '加载视频列表失败';
      }
    },
    handlePaste(event) {
      setTimeout(() => {
        this.parseShareInput(this.shareInput);
      }, 0);
    },
    async parseShareInput(input) {
      this.error = null;
      try {
        let url, title, platform;

        input = input.trim();
        
        const biliShareMatch = input.match(/【(.+?)】.*?(?:https?:\/\/)?(?:www\.)?bilibili\.com\/video\/(BV[A-Za-z0-9]+)/);
        if (biliShareMatch) {
          title = biliShareMatch[1];
          url = `https://www.bilibili.com/video/${biliShareMatch[2]}`;
          platform = 'bilibili';
        } 
        else if (input.includes('bilibili.com/video/')) {
          const biliMatch = input.match(/bilibili\.com\/video\/(BV[A-Za-z0-9]+)/);
          if (biliMatch) {
            url = `https://www.bilibili.com/video/${biliMatch[1]}`;
            platform = 'bilibili';
          }
        }
        else if (input.includes('youtube.com/') || input.includes('youtu.be/')) {
          let videoId;
          if (input.includes('youtu.be/')) {
            videoId = input.split('youtu.be/')[1];
          } else if (input.includes('/v/')) {
            videoId = input.split('/v/')[1];
          } else if (input.includes('watch?v=')) {
            videoId = input.split('watch?v=')[1];
          } else if (input.includes('embed/')) {
            videoId = input.split('embed/')[1];
          }

          if (videoId) {
            videoId = videoId.split('&')[0].split('?')[0].split('#')[0];
            url = `https://www.youtube.com/watch?v=${videoId}`;
            platform = 'youtube';
          }
        }

        if (!platform) {
          throw new Error('不支持的视频链接格式');
        }

        this.isFetchingTitle = true;
        try {
          if (!title) {
            title = await this.getVideoTitle(url, platform);
          }

          try {
            new URL(url); // Validate URL
          } catch (error) {
            throw new Error('无效的 URL 格式');
          }
          
          if (title) {
            this.newVideo = {
              url,
              title,
              platform
            };
          } else {
            throw new Error('无法获取视频标题');
          }
        } catch (error) {
          throw error;
        } finally {
          this.isFetchingTitle = false;
        }
      } catch (error) {
        console.error('Error parsing share input:', error);
        this.error = error.message || '处理链接时出错';
        this.newVideo = null;
      }
    },

    async addVideo() {
      if (!this.canAddVideo || this.isAddingVideo) return;

      if (this.videos.length >= 10) {
        this.error = '最多只能添加 10 个视频';
        return;
      }

      if (this.isDuplicateVideo) {
        this.error = '该视频已存在';
        return;
      }

      this.isAddingVideo = true;
      this.error = null;
      try {
        const thumbnailData = await this.getThumbnail({
          ...this.newVideo,
          id: Date.now().toString()
        });

        const videoData = {
          ...this.newVideo,
          id: Date.now().toString(),
          thumbnail: thumbnailData.thumbnail || null,
          thumbnailColor: thumbnailData.thumbnailColor || null
        };

        console.log('Adding video:', videoData);

        const response = await fetch('http://localhost:8000/videos', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(videoData)
        });
      
        if (response.ok) {
          console.log('Video added successfully');
          this.videos.push(videoData);
          this.shareInput = '';
          this.newVideo = null;
        } else {
          const error = await response.json();
          throw new Error(error.detail || '添加视频失败');
        }
      } catch (error) {
        console.error('Error in addVideo:', error);
        this.error = error.message || '添加视频失败';
      } finally {
        this.isAddingVideo = false;
      }
    },
    async getThumbnail(video) {
      if (video.customThumbnail) {
        return {
          thumbnail: video.customThumbnail,
          thumbnailColor: null
        };
      }
      
      if (video.platform === 'youtube') {
        let videoId;
        const url = video.url;

        if (url.includes('youtu.be/')) {
          videoId = url.split('youtu.be/')[1];
        } else if (url.includes('/v/')) {
          videoId = url.split('/v/')[1];
        } else if (url.includes('watch?v=')) {
          videoId = url.split('watch?v=')[1];
        } else if (url.includes('embed/')) {
          videoId = url.split('embed/')[1];
        }

        if (videoId) {
          videoId = videoId.split('&')[0].split('?')[0].split('#')[0];
        }

        return {
          thumbnail: videoId ? `https://img.youtube.com/vi/${videoId}/0.jpg` : '',
          thumbnailColor: null
        };
      } else if (video.platform === 'bilibili') {
        const colors = [
          '#7c9cbd', '#8b9a6d', '#917c9c', '#9c7c7c', '#7c919c',
          '#8f8f8f', '#6b8e8e', '#8e6b6b', '#6b8e6b', '#8e8e6b'
        ];
        const hash = video.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        return {
          thumbnail: '',
          thumbnailColor: colors[hash % colors.length]
        };
      }
      return {
        thumbnail: '',
        thumbnailColor: null
      };
    },
    playVideo(video) {
      if (video.platform === 'youtube') {
        let videoId;
        const url = video.url;

        if (url.includes('youtu.be/')) {
          videoId = url.split('youtu.be/')[1];
        } else if (url.includes('/v/')) {
          videoId = url.split('/v/')[1];
        } else if (url.includes('watch?v=')) {
          videoId = url.split('watch?v=')[1];
        } else if (url.includes('embed/')) {
          videoId = url.split('embed/')[1];
        }

        if (videoId) {
          videoId = videoId.split('&')[0].split('?')[0].split('#')[0];
          window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
        } else {
          window.open(url, '_blank');
        }
      } else if (video.platform === 'bilibili') {
        const bvid = video.url.match(/video\/(BV\w+)/)?.[1] || 
                    video.url.match(/BV\w+/)?.[0];
        if (bvid) {
          window.open(`https://www.bilibili.com/video/${bvid}`, '_blank');
        } else {
          window.open(video.url, '_blank');
        }
      }
    },
    removeVideo(video) {
      this.videos = this.videos.filter(v => v.id !== video.id);
    }
  }
}
</script>

<style>
.app {
  margin: 0 auto;
  padding: 24px 56px;
  width: 100%;
  max-width: 1100px;
  box-sizing: border-box;
  min-width: 900px;
}

@media (max-width: 1200px) {
  .app {
    padding: 24px 40px;
  }
}

@media (max-width: 1024px) {
  .app {
    min-width: 750px;
  }

  .video-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 850px) {
  .app {
    padding: 24px 24px;
    min-width: auto;
  }

  .video-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .video-grid {
    grid-template-columns: 1fr;
  }
}

h1 {
  color: #0f0f0f;
  margin-bottom: 32px;
  font-size: 20px;
}

.add-video-container {
  margin: 0 0 32px 0;
}

.add-video {
  display: flex;
  gap: 12px;
  background-color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}

.error-message {
  color: #cc0000;
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #ffeaea;
  border-radius: 4px;
  font-size: 0.9rem;
}

.status-message {
  color: #666666;
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f8f8f8;
  border-radius: 4px;
  font-size: 0.9rem;
}

.add-button {
  min-width: 100px;
  transition: all 0.2s ease;
  padding: 8px 16px;
  border-radius: 18px;
  border: none;
  background: #065fd4;
  color: white;
  font-size: 14px;
  cursor: pointer;
}

.add-button:hover {
  background: #0356c7;
}

.add-button.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.video-grid {
  display: grid;
  gap: 40px 16px;
  margin-top: 24px;
  grid-template-columns: repeat(4, 1fr);
  width: 100%;
}

.video-card {
  width: 100%;
  cursor: pointer;
  transition: transform 0.15s ease;
  display: flex;
  flex-direction: column;
}

.video-card:hover {
  transform: translateY(-1px);
}

.video-card:hover h3 {
  color: #065fd4;
}

.video-thumbnail-container {
  width: 100%;
  margin-bottom: 12px;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #f9f9f9;
}

.video-thumbnail {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
  background-color: #f1f1f1;
}

.bilibili-thumbnail {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  color: white;
  font-size: 15px;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
  border-radius: 0;
}

.video-info {
  padding: 0 4px;
}

.video-card h3 {
  margin: 0 0 6px 0;
  font-size: 0.95rem;
  line-height: 1.4;
  font-weight: 500;
  color: #0f0f0f;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-card p {
  margin: 0;
  color: #606060;
  font-size: 0.85rem;
  text-transform: capitalize;
}

.bilibili-thumbnail::after {
  content: "Bilibili";
}
</style>
