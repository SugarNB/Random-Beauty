import tkinter as tk
from tkinter import ttk
import vlc
import requests
import os
import threading
import time

class EnhancedVLCPlayer:
    def __init__(self, root):
        self.root = root
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.video_urls = []  # 存储视频地址列表
        self.current_index = -1  # 当前视频索引
        
        # 循环播放设置
        self.loop_single = tk.BooleanVar(value=False)  # 单视频循环
        self.loop_playlist = tk.BooleanVar(value=False)  # 播放列表循环
        self.auto_play = tk.BooleanVar(value=True)  # 自动播放
        
        # 播放状态
        self.is_playing = False
        self.update_interval = 1000  # 更新间隔(ms)
        
        # 创建视频显示区域
        self.video_frame = tk.Frame(root, bg='black')
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        # 获取窗口ID并绑定VLC
        self.win_id = self.video_frame.winfo_id()
        self.player.set_hwnd(self.win_id)
        
        # 控制面板
        self.create_controls()
        
        # 状态栏
        self.create_status_bar()
        
        # 绑定播放结束事件
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_video_end)
        
        # 如果启用自动播放，开始播放
        if self.auto_play.get():
            self.root.after(1000, self.play)
    
    def create_controls(self):
        """创建控制面板"""
        self.controls = ttk.Frame(self.root)
        self.controls.pack(fill=tk.X, pady=5)
        
        # 播放控制按钮
        play_frame = ttk.Frame(self.controls)
        play_frame.pack(side=tk.LEFT, padx=5)
        
        buttons = [
            ("播放", self.play),
            ("暂停", self.pause),
            ("停止", self.stop),
            ("上一个", self.prev_video),
            ("下一个", self.next_video),
            ("下载", self.download_video)
        ]
        
        for text, cmd in buttons:
            ttk.Button(play_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)
        
        # 循环播放控制
        loop_frame = ttk.Frame(self.controls)
        loop_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Checkbutton(loop_frame, text="单视频循环", variable=self.loop_single).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(loop_frame, text="播放列表循环", variable=self.loop_playlist).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(loop_frame, text="自动播放", variable=self.auto_play).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_frame = ttk.Frame(self.controls)
        self.progress_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(
            self.progress_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            command=self.seek_video
        )
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        # 时间显示
        self.time_label = ttk.Label(self.progress_frame, text="00:00 / 00:00")
        self.time_label.pack()
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_bar, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.video_count_label = ttk.Label(self.status_bar, text="视频数量: 0")
        self.video_count_label.pack(side=tk.RIGHT, padx=5)
    
    def fetch_video_urls(self):
        """获取API视频地址列表"""
        try:
            self.status_label.config(text="正在获取视频...")
            response = requests.get("https://api.kuleu.com/api/MP4_xiaojiejie?type=json", timeout=10)
            response.raise_for_status()
            video_url = response.json().get('mp4_video', '')
            if video_url:
                self.video_urls.append(video_url)
                self.video_count_label.config(text=f"视频数量: {len(self.video_urls)}")
                self.status_label.config(text="视频获取成功")
                return True
            else:
                self.status_label.config(text="未获取到视频地址")
                return False
        except Exception as e:
            self.status_label.config(text=f"获取视频失败: {str(e)}")
            return False
    
    def play(self):
        """播放当前视频"""
        if self.current_index == -1 or self.current_index >= len(self.video_urls):
            if not self.fetch_video_urls():
                return
            self.current_index = 0
        
        if self.video_urls:
            try:
                url = self.video_urls[self.current_index]
                media = self.instance.media_new(url)
                self.player.set_media(media)
                self.player.play()
                self.is_playing = True
                self.status_label.config(text=f"正在播放第 {self.current_index + 1} 个视频")
                
                # 开始更新进度
                self.update_progress()
            except Exception as e:
                self.status_label.config(text=f"播放失败: {str(e)}")
    
    def pause(self):
        """暂停/继续"""
        if self.is_playing:
            self.player.pause()
            self.status_label.config(text="已暂停")
        else:
            self.player.play()
            self.status_label.config(text="继续播放")
        self.is_playing = not self.is_playing
    
    def stop(self):
        """停止播放"""
        self.player.stop()
        self.is_playing = False
        self.progress_var.set(0)
        self.time_label.config(text="00:00 / 00:00")
        self.status_label.config(text="已停止")
    
    def prev_video(self):
        """播放上一个视频"""
        if self.current_index > 0:
            self.current_index -= 1
            self.play()
        else:
            self.status_label.config(text="已经是第一个视频")
    
    def next_video(self):
        """播放下一个视频"""
        self.current_index += 1
        if self.current_index >= len(self.video_urls):
            if self.loop_playlist.get():
                self.current_index = 0  # 循环到第一个
            else:
                self.fetch_video_urls()  # 获取新视频
        self.play()
    
    def seek_video(self, value):
        """跳转到指定位置"""
        if self.is_playing:
            try:
                length = self.player.get_length()
                if length > 0:
                    position = int((float(value) / 100) * length)
                    self.player.set_time(position)
            except:
                pass
    
    def update_progress(self):
        """更新进度条和时间显示"""
        if self.is_playing:
            try:
                length = self.player.get_length()
                position = self.player.get_time()
                
                if length > 0 and position >= 0:
                    # 更新进度条
                    progress = (position / length) * 100
                    self.progress_var.set(progress)
                    
                    # 更新时间显示
                    current_time = self.format_time(position)
                    total_time = self.format_time(length)
                    self.time_label.config(text=f"{current_time} / {total_time}")
            except:
                pass
            
            # 继续更新
            self.root.after(self.update_interval, self.update_progress)
    
    def format_time(self, ms):
        """格式化时间显示"""
        if ms < 0:
            return "00:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def on_video_end(self, event):
        """视频播放结束事件处理"""
        if self.loop_single.get():
            # 单视频循环
            self.root.after(100, self.play)
        elif self.loop_playlist.get():
            # 播放列表循环
            self.root.after(100, self.next_video)
        else:
            # 自动播放下一个
            self.root.after(100, self.next_video)
    
    def download_video(self):
        """下载当前视频"""
        if self.current_index >= 0 and self.current_index < len(self.video_urls):
            url = self.video_urls[self.current_index]
            try:
                self.status_label.config(text="正在下载视频...")
                
                # 创建下载目录
                download_dir = "downloaded_videos"
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                filename = os.path.join(download_dir, f"video_{self.current_index}.mp4")
                with open(filename, 'wb') as file:
                    file.write(response.content)
                
                self.status_label.config(text=f"视频已下载到: {filename}")
            except Exception as e:
                self.status_label.config(text=f"下载失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("增强版VLC播放器 - 支持自动循环播放")
    root.geometry("900x700")
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    player = EnhancedVLCPlayer(root)
    root.mainloop()