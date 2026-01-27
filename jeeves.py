"""
JEEVES AI - Personal PC Assistant
By DAXXTEAM

SciFi Cyberpunk UI | Continuous Voice | Hindi Support
Powered by Groq AI (FREE & FAST) + Edge TTS (Hindi Voice)
"""

import os
import sys
import json
import subprocess
import webbrowser
import threading
import datetime
import platform
import time
import tempfile
from pathlib import Path

# GUI
import tkinter as tk
from tkinter import scrolledtext, messagebox

# Install dependencies
def install_deps():
    deps = ['groq', 'SpeechRecognition', 'psutil', 'pillow', 'pyautogui', 'edge-tts', 'pygame']
    for pkg in deps:
        try:
            if pkg == 'edge-tts':
                __import__('edge_tts')
            elif pkg == 'SpeechRecognition':
                __import__('speech_recognition')
            else:
                __import__(pkg.lower().replace('-', '_'))
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])

install_deps()

from groq import Groq
import speech_recognition as sr
import psutil
import edge_tts
import asyncio

# For playing audio
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False


class JeevesAI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ JEEVES AI - Cyberpunk Assistant")
        self.root.geometry("1000x750")
        self.root.configure(bg='#0a0a0f')
        self.root.resizable(True, True)
        
        # Colors - Cyberpunk Theme
        self.colors = {
            'bg_dark': '#0a0a0f',
            'bg_mid': '#12121a',
            'bg_light': '#1a1a2e',
            'accent_cyan': '#00f5ff',
            'accent_magenta': '#ff00ff',
            'accent_purple': '#8b5cf6',
            'accent_green': '#00ff88',
            'accent_orange': '#ff6b35',
            'text_primary': '#ffffff',
            'text_secondary': '#a0a0b0',
            'border': '#2a2a3e',
        }
        
        # Variables
        self.api_key = tk.StringVar()
        self.continuous_listen = False
        self.client = None
        self.chat_history = []
        self.recognizer = sr.Recognizer()
        self.voice_enabled = tk.BooleanVar(value=True)
        self.is_speaking = False
        
        # Temp folder for audio
        self.temp_dir = Path(tempfile.gettempdir()) / 'jeeves_audio'
        self.temp_dir.mkdir(exist_ok=True)
        
        # Config
        self.config_file = Path.home() / '.jeeves_config.json'
        self.load_config()
        
        # Create UI
        self.create_cyberpunk_ui()
        
        # System prompt
        self.system_prompt = """Tu JEEVES hai - ek AI personal assistant jo DAXXTEAM ne banaya hai.

RULES:
- Hindi-English mix (Hinglish) mein baat kar
- User ko "Boss" bol
- Chhote aur clear answers de (1-2 lines max)
- Friendly aur helpful reh

COMMANDS (use when needed):
- CMD:OPEN_APP:<app> - App kholne ke liye
- CMD:OPEN_URL:<url> - Website kholne ke liye
- CMD:SEARCH:<query> - Google search ke liye
- CMD:SYSTEM_INFO - System info ke liye
- CMD:SCREENSHOT - Screenshot ke liye
- CMD:VOLUME:<up/down/mute> - Volume ke liye
- CMD:LOCK - PC lock ke liye

Example response: "Haan Boss, Chrome khol raha hoon! CMD:OPEN_APP:chrome"
"""

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.api_key.set(json.load(f).get('api_key', ''))
        except:
            pass
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'api_key': self.api_key.get()}, f)
        except:
            pass
    
    def create_cyberpunk_ui(self):
        main = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header = tk.Frame(main, bg=self.colors['bg_dark'])
        header.pack(fill=tk.X, pady=(0, 15))
        
        title_frame = tk.Frame(header, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT)
        
        self.icon_label = tk.Label(title_frame, text="◈", font=('Consolas', 36, 'bold'),
                                   fg=self.colors['accent_cyan'], bg=self.colors['bg_dark'])
        self.icon_label.pack(side=tk.LEFT)
        
        title_text = tk.Frame(title_frame, bg=self.colors['bg_dark'])
        title_text.pack(side=tk.LEFT, padx=(10, 0))
        
        tk.Label(title_text, text="JEEVES", font=('Consolas', 32, 'bold'),
                fg=self.colors['accent_cyan'], bg=self.colors['bg_dark']).pack(anchor='w')
        tk.Label(title_text, text="CYBERPUNK AI ASSISTANT", font=('Consolas', 10),
                fg=self.colors['accent_magenta'], bg=self.colors['bg_dark']).pack(anchor='w')
        
        # Right side - status
        right_frame = tk.Frame(header, bg=self.colors['bg_dark'])
        right_frame.pack(side=tk.RIGHT)
        
        self.voice_toggle = tk.Checkbutton(right_frame, text="🔊 VOICE", font=('Consolas', 10, 'bold'),
                                           variable=self.voice_enabled, bg=self.colors['bg_dark'],
                                           fg=self.colors['accent_green'], selectcolor=self.colors['bg_mid'],
                                           activebackground=self.colors['bg_dark'])
        self.voice_toggle.pack(side=tk.LEFT, padx=(0, 20))
        
        self.status_frame = tk.Frame(right_frame, bg=self.colors['bg_mid'], padx=15, pady=8)
        self.status_frame.pack(side=tk.LEFT)
        
        self.status_dot = tk.Label(self.status_frame, text="●", font=('Consolas', 14),
                                   fg='#ff3333', bg=self.colors['bg_mid'])
        self.status_dot.pack(side=tk.LEFT)
        
        self.status_text = tk.Label(self.status_frame, text="OFFLINE", font=('Consolas', 10, 'bold'),
                                    fg=self.colors['text_secondary'], bg=self.colors['bg_mid'])
        self.status_text.pack(side=tk.LEFT, padx=(8, 0))
        
        # API Key Bar
        api_bar = tk.Frame(main, bg=self.colors['bg_light'], padx=20, pady=15)
        api_bar.pack(fill=tk.X, pady=(0, 15))
        
        api_left = tk.Frame(api_bar, bg=self.colors['bg_light'])
        api_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(api_left, text="◆ GROQ API KEY", font=('Consolas', 9, 'bold'),
                fg=self.colors['accent_purple'], bg=self.colors['bg_light']).pack(anchor='w')
        
        api_entry_frame = tk.Frame(api_left, bg=self.colors['border'], padx=2, pady=2)
        api_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.api_entry = tk.Entry(api_entry_frame, textvariable=self.api_key, font=('Consolas', 11),
                                  bg=self.colors['bg_mid'], fg=self.colors['accent_cyan'],
                                  insertbackground=self.colors['accent_cyan'], relief=tk.FLAT, show='●')
        self.api_entry.pack(fill=tk.X, ipady=8, padx=1, pady=1)
        
        api_right = tk.Frame(api_bar, bg=self.colors['bg_light'])
        api_right.pack(side=tk.RIGHT, padx=(20, 0))
        
        self.connect_btn = tk.Button(api_right, text="▶ CONNECT", font=('Consolas', 10, 'bold'),
                                     bg=self.colors['accent_cyan'], fg='#000000', relief=tk.FLAT,
                                     padx=20, pady=8, cursor='hand2', command=self.connect_api)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(api_right, text="◈ FREE KEY", font=('Consolas', 9),
                  bg=self.colors['bg_mid'], fg=self.colors['accent_magenta'], relief=tk.FLAT,
                  padx=15, pady=8, cursor='hand2',
                  command=lambda: webbrowser.open('https://console.groq.com/keys')).pack(side=tk.LEFT)
        
        tk.Button(api_right, text="🔊 TEST", font=('Consolas', 9),
                  bg=self.colors['bg_mid'], fg=self.colors['accent_orange'], relief=tk.FLAT,
                  padx=10, pady=8, cursor='hand2', command=self.test_voice).pack(side=tk.LEFT, padx=(10, 0))
        
        # Chat Display
        chat_container = tk.Frame(main, bg=self.colors['border'], padx=2, pady=2)
        chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.chat = scrolledtext.ScrolledText(chat_container, font=('Consolas', 11),
                                              bg=self.colors['bg_mid'], fg=self.colors['text_primary'],
                                              relief=tk.FLAT, wrap=tk.WORD, padx=15, pady=15,
                                              state=tk.DISABLED, cursor='arrow')
        self.chat.pack(fill=tk.BOTH, expand=True)
        
        self.chat.tag_config('user', foreground=self.colors['accent_cyan'], font=('Consolas', 11, 'bold'))
        self.chat.tag_config('jeeves', foreground=self.colors['accent_green'], font=('Consolas', 11, 'bold'))
        self.chat.tag_config('system', foreground=self.colors['accent_orange'], font=('Consolas', 10, 'italic'))
        self.chat.tag_config('error', foreground='#ff4444')
        self.chat.tag_config('time', foreground=self.colors['text_secondary'], font=('Consolas', 9))
        
        # Input Area
        input_container = tk.Frame(main, bg=self.colors['bg_dark'])
        input_container.pack(fill=tk.X, pady=(0, 15))
        
        input_border = tk.Frame(input_container, bg=self.colors['accent_cyan'], padx=2, pady=2)
        input_border.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        self.input_entry = tk.Entry(input_border, font=('Consolas', 13),
                                    bg=self.colors['bg_mid'], fg=self.colors['text_primary'],
                                    insertbackground=self.colors['accent_cyan'], relief=tk.FLAT)
        self.input_entry.pack(fill=tk.X, ipady=12, padx=1, pady=1)
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        
        self.voice_btn = tk.Button(input_container, text="🎤 MIC OFF", font=('Consolas', 11, 'bold'),
                                   bg=self.colors['bg_light'], fg=self.colors['text_secondary'],
                                   relief=tk.FLAT, width=12, cursor='hand2', command=self.toggle_mic)
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=10)
        
        tk.Button(input_container, text="◈ SEND", font=('Consolas', 11, 'bold'),
                  bg=self.colors['accent_magenta'], fg='#ffffff', relief=tk.FLAT,
                  width=10, cursor='hand2', command=self.send_message).pack(side=tk.LEFT, ipady=10)
        
        # Quick Actions
        actions = tk.Frame(main, bg=self.colors['bg_dark'])
        actions.pack(fill=tk.X)
        
        for text, cmd in [("📁 FILES", "File Explorer kholo"), ("🌐 CHROME", "Chrome kholo"),
                          ("💻 SYSTEM", "System info dikhao"), ("📸 PHOTO", "Screenshot lo"),
                          ("🔊 VOL+", "Volume badhao"), ("🔇 MUTE", "Mute karo")]:
            tk.Button(actions, text=text, font=('Consolas', 9, 'bold'),
                     bg=self.colors['bg_light'], fg=self.colors['accent_purple'],
                     relief=tk.FLAT, padx=12, pady=6, cursor='hand2',
                     command=lambda c=cmd: self.quick_action(c)).pack(side=tk.LEFT, padx=(0, 8))
        
        # Footer
        tk.Label(main, text="◈ DAXXTEAM ◈ Groq AI ◈ Edge TTS Hindi ◈ 100% FREE ◈",
                font=('Consolas', 9), fg=self.colors['text_secondary'], 
                bg=self.colors['bg_dark']).pack(pady=(15, 0))
        
        # Welcome
        self.add_message("JEEVES", "Namaste Boss! Main JEEVES hoon. API key daalo, Connect karo, aur TEST button se awaaz check karo!", 'jeeves')
        self.animate_icon()
    
    def animate_icon(self):
        colors = [self.colors['accent_cyan'], self.colors['accent_magenta'], 
                  self.colors['accent_purple'], self.colors['accent_green']]
        def cycle():
            if hasattr(self, 'icon_label'):
                current = self.icon_label.cget('fg')
                idx = colors.index(current) if current in colors else 0
                self.icon_label.config(fg=colors[(idx + 1) % len(colors)])
                self.root.after(1000, cycle)
        cycle()
    
    def add_message(self, sender, message, tag='user'):
        self.chat.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.chat.insert(tk.END, f"\n[{timestamp}] ", 'time')
        self.chat.insert(tk.END, f"{sender}: ", tag)
        self.chat.insert(tk.END, f"{message}\n")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)
    
    def test_voice(self):
        """Test voice output"""
        self.add_message("SYSTEM", "Testing voice... 🔊", 'system')
        threading.Thread(target=lambda: self.speak("Namaste Boss! Main JEEVES hoon. Meri awaaz aa rahi hai!"), daemon=True).start()
    
    def speak(self, text):
        """Speak using Edge TTS (Microsoft voices - works great!)"""
        if not self.voice_enabled.get() or self.is_speaking:
            return
        
        if not text or len(text.strip()) < 2:
            return
        
        # Clean text
        clean = text[:500]
        for skip in ['CMD:', 'http', 'https', '━', '◈', '●', '**', '__', '\n']:
            clean = clean.replace(skip, ' ')
        clean = ' '.join(clean.split())
        
        if not clean:
            return
        
        self.is_speaking = True
        
        try:
            # Generate audio file
            audio_file = self.temp_dir / f"speech_{int(time.time())}.mp3"
            
            # Use Edge TTS - Hindi voice
            async def generate():
                # Hindi female voice - sounds natural
                communicate = edge_tts.Communicate(clean, "hi-IN-SwaraNeural")
                await communicate.save(str(audio_file))
            
            # Run async
            asyncio.run(generate())
            
            # Play audio
            if audio_file.exists():
                if PYGAME_AVAILABLE:
                    pygame.mixer.music.load(str(audio_file))
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                else:
                    # Fallback: use system player
                    if platform.system() == 'Windows':
                        os.system(f'start /min wmplayer "{audio_file}"')
                        time.sleep(3)
                
                # Cleanup
                try:
                    audio_file.unlink()
                except:
                    pass
                    
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            self.is_speaking = False
    
    def connect_api(self):
        api_key = self.api_key.get().strip()
        if not api_key:
            messagebox.showerror("Error", "API key daalo!")
            return
        
        try:
            self.client = Groq(api_key=api_key)
            self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            
            self.chat_history = [{"role": "system", "content": self.system_prompt}]
            
            self.status_dot.config(fg=self.colors['accent_green'])
            self.status_text.config(text="ONLINE", fg=self.colors['accent_green'])
            self.connect_btn.config(text="✓ CONNECTED", bg=self.colors['accent_green'])
            
            self.save_config()
            self.add_message("SYSTEM", "Connected! Ab bolo ya likho.", 'system')
            threading.Thread(target=lambda: self.speak("JEEVES online ho gaya Boss! Bolo, main sun raha hoon!"), daemon=True).start()
            
        except Exception as e:
            self.status_dot.config(fg='#ff3333')
            messagebox.showerror("Error", f"Connect fail: {str(e)}")
    
    def send_message(self):
        message = self.input_entry.get().strip()
        if not message or not self.client:
            return
        
        self.input_entry.delete(0, tk.END)
        self.add_message("You", message, 'user')
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
    
    def process_message(self, message):
        try:
            self.chat_history.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.chat_history,
                max_tokens=256,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content
            self.chat_history.append({"role": "assistant", "content": reply})
            
            if len(self.chat_history) > 20:
                self.chat_history = [self.chat_history[0]] + self.chat_history[-18:]
            
            self.execute_commands(reply)
            
            # Clean for display
            display = reply
            for cmd in ['CMD:OPEN_APP:', 'CMD:OPEN_URL:', 'CMD:SEARCH:', 'CMD:SYSTEM_INFO', 
                       'CMD:SCREENSHOT', 'CMD:VOLUME:', 'CMD:LOCK']:
                if cmd in display:
                    idx = display.find(cmd)
                    end = display.find('\n', idx) if '\n' in display[idx:] else len(display)
                    display = display[:idx] + display[end:]
            
            display = display.strip()
            self.root.after(0, lambda: self.add_message("JEEVES", display, 'jeeves'))
            
            # SPEAK
            if display:
                self.speak(display)
            
        except Exception as e:
            self.root.after(0, lambda: self.add_message("SYSTEM", f"Error: {str(e)}", 'error'))
    
    def execute_commands(self, text):
        system = platform.system()
        
        if 'CMD:OPEN_APP:' in text:
            app = text.split('CMD:OPEN_APP:')[1].split('\n')[0].strip().lower()
            try:
                apps = {'chrome': 'chrome', 'firefox': 'firefox', 'edge': 'msedge',
                       'notepad': 'notepad', 'calculator': 'calc', 'explorer': 'explorer',
                       'file explorer': 'explorer', 'cmd': 'cmd', 'vscode': 'code'}
                subprocess.Popen(apps.get(app, app), shell=True)
            except:
                pass
        
        if 'CMD:OPEN_URL:' in text:
            url = text.split('CMD:OPEN_URL:')[1].split('\n')[0].strip()
            webbrowser.open(url if url.startswith('http') else 'https://' + url)
        
        if 'CMD:SEARCH:' in text:
            query = text.split('CMD:SEARCH:')[1].split('\n')[0].strip()
            webbrowser.open(f'https://www.google.com/search?q={query}')
        
        if 'CMD:SYSTEM_INFO' in text:
            try:
                info = f"OS: {platform.system()} | CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"
                self.root.after(0, lambda: self.add_message("SYSTEM", info, 'system'))
            except:
                pass
        
        if 'CMD:SCREENSHOT' in text:
            try:
                import pyautogui
                path = Path.home() / 'Desktop' / f'screenshot_{int(time.time())}.png'
                pyautogui.screenshot(str(path))
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Screenshot saved: {path.name}", 'system'))
            except:
                pass
        
        if 'CMD:VOLUME:' in text:
            try:
                import pyautogui
                action = text.split('CMD:VOLUME:')[1].split('\n')[0].strip().lower()
                if action == 'up':
                    pyautogui.press('volumeup', presses=5)
                elif action == 'down':
                    pyautogui.press('volumedown', presses=5)
                elif action == 'mute':
                    pyautogui.press('volumemute')
            except:
                pass
        
        if 'CMD:LOCK' in text and system == 'Windows':
            os.system('rundll32.exe user32.dll,LockWorkStation')
    
    def toggle_mic(self):
        if self.continuous_listen:
            self.continuous_listen = False
            self.voice_btn.config(text="🎤 MIC OFF", bg=self.colors['bg_light'], 
                                 fg=self.colors['text_secondary'])
        else:
            if not self.client:
                messagebox.showwarning("!", "Pehle Connect karo!")
                return
            self.continuous_listen = True
            self.voice_btn.config(text="🔴 MIC ON", bg=self.colors['accent_magenta'], fg='#ffffff')
            threading.Thread(target=self.listen_loop, daemon=True).start()
    
    def listen_loop(self):
        while self.continuous_listen:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    self.root.after(0, lambda: self.add_message("SYSTEM", "🎧 Listening...", 'system'))
                    
                    try:
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        try:
                            text = self.recognizer.recognize_google(audio, language='hi-IN')
                        except:
                            text = self.recognizer.recognize_google(audio, language='en-IN')
                        
                        if text and self.continuous_listen:
                            self.root.after(0, lambda t=text: self._process_voice(t))
                            time.sleep(2)
                    except:
                        pass
            except:
                time.sleep(1)
    
    def _process_voice(self, text):
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, text)
        self.send_message()
    
    def quick_action(self, action):
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, action)
        self.send_message()


def main():
    root = tk.Tk()
    app = JeevesAI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
