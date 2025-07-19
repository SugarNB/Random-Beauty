import tkinter as tk
import vlc
import requests
import os

class EnhancedVLCPlayer:
    def __init__(self, root):
        self.root = root
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.video_urls = []  # 存储视频地址列表
        self.current_index = -1  # 当前视频索引
        
        # 创建视频显示区域
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # 获取窗口ID并绑定VLC
        self.win_id = self.frame.winfo_id()
        self.player.set_hwnd(self.win_id)
        
        # 控制按钮
        self.controls = tk.Frame(root)
        self.controls.pack(fill=tk.X)
        
        tk.Button(self.controls, text="播放", command=self.play).pack(side=tk.LEFT)
        tk.Button(self.controls, text="暂停", command=self.pause).pack(side=tk.LEFT)
        tk.Button(self.controls, text="停止", command=self.stop).pack(side=tk.LEFT)
        tk.Button(self.controls, text="上一个视频", command=self.prev_video).pack(side=tk.LEFT)
        tk.Button(self.controls, text="下一个视频", command=self.next_video).pack(side=tk.LEFT)
        tk.Button(self.controls, text="下载", command=self.download_video).pack(side=tk.LEFT)
    
    def fetch_video_urls(self):
        """获取API视频地址列表"""
        response = requests.get("https://api.kuleu.com/api/MP4_xiaojiejie?type=json")
        video_url = response.json().get('mp4_video', '')
        if video_url:
            self.video_urls.append(video_url)
    
    def play(self):
        """播放当前视频"""
        if self.current_index == -1 or self.current_index >= len(self.video_urls):
            self.fetch_video_urls()
            self.current_index = 0
        
        if self.video_urls:
            url = self.video_urls[self.current_index]
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
    
    def pause(self):
        """暂停/继续"""
        self.player.pause()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
    
    def prev_video(self):
        """播放上一个视频"""
        if self.current_index > 0:
            self.current_index -= 1
            self.play()

    def next_video(self):
        """播放下一个视频"""
        self.current_index += 1
        if self.current_index >= len(self.video_urls):
            self.fetch_video_urls()
        self.play()
    
    def download_video(self):
        """下载当前视频"""
        if self.current_index >= 0 and self.current_index < len(self.video_urls):
            url = self.video_urls[self.current_index]
            response = requests.get(url)
            filename = os.path.join(os.getcwd(), f"video_{self.current_index}.mp4")
            with open(filename, 'wb') as file:
                file.write(response.content)
            print(f"视频已下载到: {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    player = EnhancedVLCPlayer(root)
    root.mainloop()