import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import vlc
import requests
import os
import json
import threading
import time
from datetime import datetime
import webbrowser

class AdvancedVLCPlayer:
    def __init__(self, root):
        self.root = root
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.video_urls = []  # 存储视频地址列表
        self.current_index = -1  # 当前视频索引
        
        # 播放设置
        self.loop_single = tk.BooleanVar(value=False)  # 单视频循环
        self.loop_playlist = tk.BooleanVar(value=True)  # 播放列表循环
        self.auto_play = tk.BooleanVar(value=True)  # 自动播放
        self.shuffle_mode = tk.BooleanVar(value=False)  # 随机播放
        
        # 播放状态
        self.is_playing = False
        self.is_fullscreen = False
        self.update_interval = 500  # 更新间隔(ms)
        
        # 播放历史
        self.play_history = []
        self.favorites = []
        self.load_data()
        
        # 创建界面
        self.create_menu()
        self.create_video_frame()
        self.create_controls()
        self.create_status_bar()
        self.create_playlist_panel()
        
        # 绑定事件
        self.bind_events()
        
        # 自动播放
        if self.auto_play.get():
            self.root.after(1000, self.play)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开本地视频", command=self.open_local_video)
        file_menu.add_command(label="保存播放列表", command=self.save_playlist)
        file_menu.add_command(label="加载播放列表", command=self.load_playlist)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 播放菜单
        play_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="播放", menu=play_menu)
        play_menu.add_command(label="播放/暂停", command=self.pause, accelerator="Space")
        play_menu.add_command(label="停止", command=self.stop)
        play_menu.add_command(label="上一个", command=self.prev_video, accelerator="←")
        play_menu.add_command(label="下一个", command=self.next_video, accelerator="→")
        play_menu.add_separator()
        play_menu.add_checkbutton(label="单视频循环", variable=self.loop_single)
        play_menu.add_checkbutton(label="播放列表循环", variable=self.loop_playlist)
        play_menu.add_checkbutton(label="随机播放", variable=self.shuffle_mode)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="全屏", command=self.toggle_fullscreen, accelerator="F11")
        view_menu.add_command(label="显示播放列表", command=self.toggle_playlist)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="播放历史", command=self.show_history)
        tools_menu.add_command(label="收藏夹", command=self.show_favorites)
        tools_menu.add_command(label="下载管理", command=self.show_downloads)
    
    def create_video_frame(self):
        """创建视频显示区域"""
        self.video_frame = tk.Frame(self.root, bg='black')
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        # 获取窗口ID并绑定VLC
        self.win_id = self.video_frame.winfo_id()
        self.player.set_hwnd(self.win_id)
    
    def create_controls(self):
        """创建控制面板"""
        self.controls = ttk.Frame(self.root)
        self.controls.pack(fill=tk.X, pady=5)
        
        # 播放控制按钮
        play_frame = ttk.Frame(self.controls)
        play_frame.pack(side=tk.LEFT, padx=5)
        
        buttons = [
            ("⏮", self.prev_video, "上一个"),
            ("⏯", self.pause, "播放/暂停"),
            ("⏹", self.stop, "停止"),
            ("⏭", self.next_video, "下一个"),
            ("📥", self.download_video, "下载"),
            ("❤", self.add_to_favorites, "收藏")
        ]
        
        for symbol, cmd, tooltip in buttons:
            btn = ttk.Button(play_frame, text=symbol, command=cmd, width=3)
            btn.pack(side=tk.LEFT, padx=2)
            self.create_tooltip(btn, tooltip)
        
        # 循环播放控制
        loop_frame = ttk.Frame(self.controls)
        loop_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Checkbutton(loop_frame, text="🔁单循环", variable=self.loop_single).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(loop_frame, text="🔁列表循环", variable=self.loop_playlist).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(loop_frame, text="🔀随机", variable=self.shuffle_mode).pack(side=tk.LEFT, padx=5)
        
        # 音量控制
        volume_frame = ttk.Frame(self.controls)
        volume_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(volume_frame, text="🔊").pack(side=tk.LEFT)
        self.volume_var = tk.IntVar(value=100)
        volume_scale = ttk.Scale(
            volume_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            command=self.set_volume,
            length=100
        )
        volume_scale.pack(side=tk.LEFT, padx=5)
        
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
        
        self.current_video_label = ttk.Label(self.status_bar, text="")
        self.current_video_label.pack(side=tk.RIGHT, padx=5)
    
    def create_playlist_panel(self):
        """创建播放列表面板"""
        self.playlist_frame = ttk.Frame(self.root, width=300)
        self.playlist_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(self.playlist_frame, text="播放列表", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 播放列表
        self.playlist_tree = ttk.Treeview(self.playlist_frame, columns=("序号", "状态"), show="tree headings", height=15)
        self.playlist_tree.heading("#0", text="视频")
        self.playlist_tree.heading("序号", text="序号")
        self.playlist_tree.heading("状态", text="状态")
        self.playlist_tree.column("#0", width=200)
        self.playlist_tree.column("序号", width=50)
        self.playlist_tree.column("状态", width=50)
        self.playlist_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 播放列表控制按钮
        playlist_controls = ttk.Frame(self.playlist_frame)
        playlist_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(playlist_controls, text="清空列表", command=self.clear_playlist).pack(side=tk.LEFT, padx=2)
        ttk.Button(playlist_controls, text="刷新", command=self.refresh_videos).pack(side=tk.LEFT, padx=2)
    
    def bind_events(self):
        """绑定事件"""
        # 键盘快捷键
        self.root.bind("<space>", lambda e: self.pause())
        self.root.bind("<Left>", lambda e: self.prev_video())
        self.root.bind("<Right>", lambda e: self.next_video())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())
        
        # 播放列表双击事件
        self.playlist_tree.bind("<Double-1>", self.on_playlist_double_click)
        
        # 播放结束事件
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_video_end)
    
    def create_tooltip(self, widget, text):
        """创建工具提示"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind("<Leave>", lambda e: hide_tooltip())
        
        widget.bind("<Enter>", show_tooltip)
    
    def fetch_video_urls(self):
        """获取API视频地址列表"""
        try:
            self.status_label.config(text="正在获取视频...")
            response = requests.get("https://api.kuleu.com/api/MP4_xiaojiejie?type=json", timeout=10)
            response.raise_for_status()
            video_url = response.json().get('mp4_video', '')
            if video_url:
                self.video_urls.append(video_url)
                self.update_playlist()
                self.video_count_label.config(text=f"视频数量: {len(self.video_urls)}")
                self.status_label.config(text="视频获取成功")
                return True
            else:
                self.status_label.config(text="未获取到视频地址")
                return False
        except Exception as e:
            self.status_label.config(text=f"获取视频失败: {str(e)}")
            return False
    
    def update_playlist(self):
        """更新播放列表显示"""
        # 清空现有项目
        for item in self.playlist_tree.get_children():
            self.playlist_tree.delete(item)
        
        # 添加视频项目
        for i, url in enumerate(self.video_urls):
            status = "▶" if i == self.current_index else "⏸"
            self.playlist_tree.insert("", "end", text=f"视频 {i+1}", values=(i+1, status))
    
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
                
                # 设置音量
                self.player.audio_set_volume(self.volume_var.get())
                
                # 更新状态
                self.status_label.config(text=f"正在播放第 {self.current_index + 1} 个视频")
                self.current_video_label.config(text=f"当前: 视频 {self.current_index + 1}")
                
                # 添加到播放历史
                self.add_to_history(url)
                
                # 更新播放列表
                self.update_playlist()
                
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
        self.update_playlist()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
        self.is_playing = False
        self.progress_var.set(0)
        self.time_label.config(text="00:00 / 00:00")
        self.status_label.config(text="已停止")
        self.update_playlist()
    
    def prev_video(self):
        """播放上一个视频"""
        if self.current_index > 0:
            self.current_index -= 1
            self.play()
        else:
            self.status_label.config(text="已经是第一个视频")
    
    def next_video(self):
        """播放下一个视频"""
        if self.shuffle_mode.get():
            # 随机播放
            import random
            if len(self.video_urls) > 1:
                new_index = random.randint(0, len(self.video_urls) - 1)
                while new_index == self.current_index and len(self.video_urls) > 1:
                    new_index = random.randint(0, len(self.video_urls) - 1)
                self.current_index = new_index
            else:
                self.current_index += 1
        else:
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
    
    def set_volume(self, value):
        """设置音量"""
        try:
            volume = int(float(value))
            self.player.audio_set_volume(volume)
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
    
    def on_playlist_double_click(self, event):
        """播放列表双击事件"""
        selection = self.playlist_tree.selection()
        if selection:
            item = self.playlist_tree.item(selection[0])
            index = int(item['values'][0]) - 1
            if 0 <= index < len(self.video_urls):
                self.current_index = index
                self.play()
    
    def toggle_fullscreen(self):
        """切换全屏"""
        if not self.is_fullscreen:
            self.root.attributes('-fullscreen', True)
            self.is_fullscreen = True
        else:
            self.exit_fullscreen()
    
    def exit_fullscreen(self):
        """退出全屏"""
        self.root.attributes('-fullscreen', False)
        self.is_fullscreen = False
    
    def toggle_playlist(self):
        """切换播放列表显示"""
        if self.playlist_frame.winfo_viewable():
            self.playlist_frame.pack_forget()
        else:
            self.playlist_frame.pack(side=tk.RIGHT, fill=tk.Y)
    
    def add_to_history(self, url):
        """添加到播放历史"""
        history_item = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'index': self.current_index
        }
        self.play_history.append(history_item)
        
        # 限制历史记录数量
        if len(self.play_history) > 100:
            self.play_history = self.play_history[-100:]
        
        self.save_data()
    
    def add_to_favorites(self):
        """添加到收藏夹"""
        if self.current_index >= 0 and self.current_index < len(self.video_urls):
            url = self.video_urls[self.current_index]
            if url not in self.favorites:
                self.favorites.append(url)
                self.save_data()
                self.status_label.config(text="已添加到收藏夹")
            else:
                self.status_label.config(text="已在收藏夹中")
    
    def show_history(self):
        """显示播放历史"""
        history_window = tk.Toplevel(self.root)
        history_window.title("播放历史")
        history_window.geometry("600x400")
        
        tree = ttk.Treeview(history_window, columns=("时间", "序号"), show="tree headings")
        tree.heading("#0", text="视频")
        tree.heading("时间", text="播放时间")
        tree.heading("序号", text="序号")
        
        for item in reversed(self.play_history):
            tree.insert("", "end", text=f"视频 {item['index']+1}", 
                       values=(item['timestamp'][:19], item['index']+1))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def show_favorites(self):
        """显示收藏夹"""
        favorites_window = tk.Toplevel(self.root)
        favorites_window.title("收藏夹")
        favorites_window.geometry("600x400")
        
        tree = ttk.Treeview(favorites_window, columns=("序号",), show="tree headings")
        tree.heading("#0", text="视频")
        tree.heading("序号", text="序号")
        
        for i, url in enumerate(self.favorites):
            tree.insert("", "end", text=f"收藏视频 {i+1}", values=(i+1,))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def show_downloads(self):
        """显示下载管理"""
        download_dir = "downloaded_videos"
        if os.path.exists(download_dir):
            os.startfile(download_dir)
        else:
            messagebox.showinfo("提示", "下载目录不存在")
    
    def open_local_video(self):
        """打开本地视频"""
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.video_urls.append(file_path)
            self.update_playlist()
            if self.current_index == -1:
                self.current_index = 0
                self.play()
    
    def save_playlist(self):
        """保存播放列表"""
        file_path = filedialog.asksaveasfilename(
            title="保存播放列表",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            playlist_data = {
                'videos': self.video_urls,
                'current_index': self.current_index,
                'settings': {
                    'loop_single': self.loop_single.get(),
                    'loop_playlist': self.loop_playlist.get(),
                    'auto_play': self.auto_play.get(),
                    'shuffle_mode': self.shuffle_mode.get()
                }
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "播放列表已保存")
    
    def load_playlist(self):
        """加载播放列表"""
        file_path = filedialog.askopenfilename(
            title="加载播放列表",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    playlist_data = json.load(f)
                
                self.video_urls = playlist_data.get('videos', [])
                self.current_index = playlist_data.get('current_index', -1)
                
                settings = playlist_data.get('settings', {})
                self.loop_single.set(settings.get('loop_single', False))
                self.loop_playlist.set(settings.get('loop_playlist', True))
                self.auto_play.set(settings.get('auto_play', True))
                self.shuffle_mode.set(settings.get('shuffle_mode', False))
                
                self.update_playlist()
                self.video_count_label.config(text=f"视频数量: {len(self.video_urls)}")
                messagebox.showinfo("成功", "播放列表已加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载播放列表失败: {str(e)}")
    
    def clear_playlist(self):
        """清空播放列表"""
        if messagebox.askyesno("确认", "确定要清空播放列表吗？"):
            self.video_urls.clear()
            self.current_index = -1
            self.update_playlist()
            self.video_count_label.config(text="视频数量: 0")
            self.status_label.config(text="播放列表已清空")
    
    def refresh_videos(self):
        """刷新视频列表"""
        self.fetch_video_urls()
    
    def load_data(self):
        """加载数据"""
        try:
            if os.path.exists('player_data.json'):
                with open('player_data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.play_history = data.get('history', [])
                    self.favorites = data.get('favorites', [])
        except:
            pass
    
    def save_data(self):
        """保存数据"""
        try:
            data = {
                'history': self.play_history,
                'favorites': self.favorites
            }
            with open('player_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
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
                
                filename = os.path.join(download_dir, f"video_{self.current_index}_{int(time.time())}.mp4")
                with open(filename, 'wb') as file:
                    file.write(response.content)
                
                self.status_label.config(text=f"视频已下载到: {filename}")
                messagebox.showinfo("下载完成", f"视频已下载到:\n{filename}")
            except Exception as e:
                self.status_label.config(text=f"下载失败: {str(e)}")
                messagebox.showerror("下载失败", f"下载失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("高级VLC播放器 v5.0 - 支持自动循环播放")
    root.geometry("1200x800")
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    player = AdvancedVLCPlayer(root)
    root.mainloop() 