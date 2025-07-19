import tkinter as tk
import vlc
import requests

class VLCPlayer:
    def __init__(self, root):
        self.root = root
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
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
    
    def get_video_url(self):
        """获取API视频地址"""
        response = requests.get("https://api.kuleu.com/api/MP4_xiaojiejie?type=json")
        return response.json().get('mp4_video', '')
    
    def play(self):
        """播放视频"""
        url = self.get_video_url()
        if url:
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
    
    def pause(self):
        """暂停/继续"""
        self.player.pause()
    
    def stop(self):
        """停止播放"""
        self.player.stop()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    player = VLCPlayer(root)
    root.mainloop()