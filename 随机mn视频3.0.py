import tkinter as tk
from tkinter import ttk
import vlc
import requests
import os

class EnhancedVLCPlayer:
    POLL_INTERVAL = 1000  # ms, adjust for smoother performance

    def __init__(self, root):
        self.root = root
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.video_urls = []
        self.current_index = -1
        self.updating = False
        self.user_dragging = False
        self.last_length = 0

        # 视频显示区域
        self.video_frame = tk.Frame(root, bg='black')
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        self.win_id = self.video_frame.winfo_id()
        self.player.set_hwnd(self.win_id)

        # 控制面板
        self.controls = ttk.Frame(root)
        self.controls.pack(fill=tk.X, pady=5)
        buttons = [
            ("播放", self.play), ("暂停", self.pause), ("停止", self.stop),
            ("上一个", self.prev_video), ("下一个", self.next_video), ("下载", self.download_video)
        ]
        for text, cmd in buttons:
            ttk.Button(self.controls, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        # 进度条
        self.scale = ttk.Scale(self.controls, from_=0, to=1000, orient=tk.HORIZONTAL, length=400)
        self.scale.pack(side=tk.LEFT, padx=10)
        self.scale.bind("<ButtonPress-1>", self.on_drag_start)
        self.scale.bind("<ButtonRelease-1>", self.on_drag_end)

        # 时长标签
        self.time_label = ttk.Label(self.controls, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT)

    def fetch_video_urls(self):
        try:
            resp = requests.get("https://api.kuleu.com/api/MP4_xiaojiejie?type=json", timeout=5)
            resp.raise_for_status()
            video_url = resp.json().get('mp4_video')
            if video_url:
                self.video_urls.append(video_url)
        except Exception as e:
            print(f"获取视频地址失败: {e}")

    def play(self):
        if self.current_index < 0 or self.current_index >= len(self.video_urls):
            self.fetch_video_urls()
            self.current_index = 0
        if not self.video_urls:
            return
        media = self.instance.media_new(self.video_urls[self.current_index])
        self.player.set_media(media)
        self.player.play()
        self.root.after(1000, self.start_update)

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()
        self.stop_update()
        self.scale.set(0)
        self.time_label.config(text="00:00 / 00:00")

    def prev_video(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.play()

    def next_video(self):
        self.current_index += 1
        if self.current_index >= len(self.video_urls):
            self.fetch_video_urls()
        self.play()

    def download_video(self):
        if 0 <= self.current_index < len(self.video_urls):
            url = self.video_urls[self.current_index]
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                filename = os.path.join(os.getcwd(), f"video_{self.current_index}.mp4")
                with open(filename, 'wb') as f:
                    f.write(resp.content)
                print(f"已下载: {filename}")
            except Exception as e:
                print(f"下载失败: {e}")

    def start_update(self):
        if not self.updating:
            self.updating = True
            self.update_progress()

    def stop_update(self):
        self.updating = False

    def update_progress(self):
        if not self.updating:
            return
        length = self.player.get_length()  # ms
        pos = self.player.get_time()       # ms
        if length > 0:
            # 只在长度变化时更新 scale 最大值
            if length != self.last_length:
                self.scale.config(to=length)
                self.last_length = length
            # 仅在用户未拖动时更新进度
            if not self.user_dragging:
                self.scale.set(pos)
            # 更新时间标签
            current = self.format_time(pos)
            total = self.format_time(length)
            self.time_label.config(text=f"{current} / {total}")
        self.root.after(self.POLL_INTERVAL, self.update_progress)

    def on_drag_start(self, event):
        self.user_dragging = True

    def on_drag_end(self, event):
        try:
            value = self.scale.get()
            self.player.set_time(int(value))
        except Exception:
            pass
        finally:
            self.user_dragging = False

    @staticmethod
    def format_time(ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Enhanced VLC Player")
    root.geometry("800x600")
    EnhancedVLCPlayer(root)
    root.mainloop()
