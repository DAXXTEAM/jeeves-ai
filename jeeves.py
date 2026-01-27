"""
JEEVES AI - Personal PC Assistant
By DAXXTEAM

SciFi Cyberpunk UI | Continuous Voice | Hindi Support
Powered by Groq AI (FREE & FAST)
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
from pathlib import Path

# GUI
import tkinter as tk
from tkinter import scrolledtext, messagebox
import tkinter.font as tkfont

# Install dependencies
def install_deps():
    deps = {'groq': 'groq', 'SpeechRecognition': 'speech_recognition', 'pyttsx3': 'pyttsx3', 
            'psutil': 'psutil', 'pillow': 'PIL', 'pyautogui': 'pyautogui'}
    for pkg, imp in deps.items():
        try:
            __import__(imp.split('.')[0])
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])

install_deps()

from groq import Groq
import speech_recognition as sr
import pyttsx3
import psutil


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
            'glow_cyan': '#00f5ff',
            'glow_pink': '#ff00ff',
        }
        
        # Variables
        self.api_key = tk.StringVar()
        self.is_listening = False
        self.continuous_listen = False
        self.client = None
        self.chat_history = []
        self.tts_engine = None
        self.recognizer = sr.Recognizer()
        
        # Config
        self.config_file = Path.home() / '.jeeves_config.json'
        self.load_config()
        
        # Init TTS with Hindi
        self.init_tts()
        
        # Create UI
        self.create_cyberpunk_ui()
        
        # System prompt - Hindi friendly
        self.system_prompt = """Tu JEEVES hai - ek advanced AI personal assistant jo DAXXTEAM ne banaya hai. Tu Hindi aur English dono mein baat kar sakta hai.

PERSONALITY:
- Friendly aur helpful reh
- User ko "Boss" ya "Sir" bol
- Thoda witty aur fun reh
- Short aur clear answers de
- Hindi-English mix (Hinglish) use kar sakta hai

SYSTEM COMMANDS (prefix with CMD:):
- CMD:OPEN_APP:<app_name> - Apps open karne ke liye
- CMD:OPEN_URL:<url> - Websites open karne ke liye
- CMD:SEARCH:<query> - Google search ke liye
- CMD:SYSTEM_INFO - System info ke liye
- CMD:SCREENSHOT - Screenshot lene ke liye
- CMD:VOLUME:<up/down/mute> - Volume control ke liye
- CMD:LOCK - PC lock karne ke liye

Example: "Chrome open kar raha hoon, Boss! CMD:OPEN_APP:chrome"

Hamesha pehle explain kar, phir command de. Hindi mein naturally baat kar jaise ek Indian friend karta hai."""

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get('api_key', ''))
        except:
            pass
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'api_key': self.api_key.get()}, f)
        except:
            pass
    
    def init_tts(self):
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            # Try to find Hindi/Indian voice
            for voice in voices:
                voice_name = voice.name.lower()
                if 'hindi' in voice_name or 'indian' in voice_name or 'zira' in voice_name:
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            self.tts_engine.setProperty('rate', 160)  # Slower for clarity
            self.tts_engine.setProperty('volume', 1.0)
        except Exception as e:
            print(f"TTS Error: {e}")
            self.tts_engine = None
    
    def create_cyberpunk_ui(self):
        # Main container with gradient effect
        main = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # ===== HEADER =====
        header = tk.Frame(main, bg=self.colors['bg_dark'])
        header.pack(fill=tk.X, pady=(0, 15))
        
        # Cyberpunk title with glow effect
        title_frame = tk.Frame(header, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT)
        
        # Animated icon
        self.icon_label = tk.Label(title_frame, text="◈", font=('Consolas', 36, 'bold'),
                                   fg=self.colors['accent_cyan'], bg=self.colors['bg_dark'])
        self.icon_label.pack(side=tk.LEFT)
        
        title_text = tk.Frame(title_frame, bg=self.colors['bg_dark'])
        title_text.pack(side=tk.LEFT, padx=(10, 0))
        
        tk.Label(title_text, text="JEEVES", font=('Consolas', 32, 'bold'),
                fg=self.colors['accent_cyan'], bg=self.colors['bg_dark']).pack(anchor='w')
        tk.Label(title_text, text="AI PERSONAL ASSISTANT", font=('Consolas', 10),
                fg=self.colors['accent_magenta'], bg=self.colors['bg_dark']).pack(anchor='w')
        
        # Status indicator
        self.status_frame = tk.Frame(header, bg=self.colors['bg_mid'], padx=15, pady=8)
        self.status_frame.pack(side=tk.RIGHT)
        
        self.status_dot = tk.Label(self.status_frame, text="●", font=('Consolas', 14),
                                   fg='#ff3333', bg=self.colors['bg_mid'])
        self.status_dot.pack(side=tk.LEFT)
        
        self.status_text = tk.Label(self.status_frame, text="OFFLINE", font=('Consolas', 10, 'bold'),
                                    fg=self.colors['text_secondary'], bg=self.colors['bg_mid'])
        self.status_text.pack(side=tk.LEFT, padx=(8, 0))
        
        # ===== API KEY BAR =====
        api_bar = tk.Frame(main, bg=self.colors['bg_light'], padx=20, pady=15)
        api_bar.pack(fill=tk.X, pady=(0, 15))
        
        # Left side - API input
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
        
        # Right side - Buttons
        api_right = tk.Frame(api_bar, bg=self.colors['bg_light'])
        api_right.pack(side=tk.RIGHT, padx=(20, 0))
        
        self.connect_btn = tk.Button(api_right, text="▶ CONNECT", font=('Consolas', 10, 'bold'),
                                     bg=self.colors['accent_cyan'], fg='#000000', relief=tk.FLAT,
                                     padx=20, pady=8, cursor='hand2', command=self.connect_api,
                                     activebackground=self.colors['accent_green'])
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        get_key_btn = tk.Button(api_right, text="◈ GET FREE KEY", font=('Consolas', 9),
                                bg=self.colors['bg_mid'], fg=self.colors['accent_magenta'], relief=tk.FLAT,
                                padx=15, pady=8, cursor='hand2',
                                command=lambda: webbrowser.open('https://console.groq.com/keys'))
        get_key_btn.pack(side=tk.LEFT)
        
        # ===== CHAT DISPLAY =====
        chat_container = tk.Frame(main, bg=self.colors['border'], padx=2, pady=2)
        chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.chat = scrolledtext.ScrolledText(chat_container, font=('Consolas', 11),
                                              bg=self.colors['bg_mid'], fg=self.colors['text_primary'],
                                              relief=tk.FLAT, wrap=tk.WORD, padx=15, pady=15,
                                              state=tk.DISABLED, cursor='arrow')
        self.chat.pack(fill=tk.BOTH, expand=True)
        
        # Chat tags
        self.chat.tag_config('user', foreground=self.colors['accent_cyan'], font=('Consolas', 11, 'bold'))
        self.chat.tag_config('jeeves', foreground=self.colors['accent_green'], font=('Consolas', 11, 'bold'))
        self.chat.tag_config('system', foreground=self.colors['accent_orange'], font=('Consolas', 10, 'italic'))
        self.chat.tag_config('error', foreground='#ff4444')
        self.chat.tag_config('time', foreground=self.colors['text_secondary'], font=('Consolas', 9))
        
        # ===== INPUT AREA =====
        input_container = tk.Frame(main, bg=self.colors['bg_dark'])
        input_container.pack(fill=tk.X, pady=(0, 15))
        
        # Input field with border
        input_border = tk.Frame(input_container, bg=self.colors['accent_cyan'], padx=2, pady=2)
        input_border.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        self.input_entry = tk.Entry(input_border, font=('Consolas', 13),
                                    bg=self.colors['bg_mid'], fg=self.colors['text_primary'],
                                    insertbackground=self.colors['accent_cyan'], relief=tk.FLAT)
        self.input_entry.pack(fill=tk.X, ipady=12, padx=1, pady=1)
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        
        # Voice button - Cyberpunk style
        self.voice_btn = tk.Button(input_container, text="🎤 MIC OFF", font=('Consolas', 11, 'bold'),
                                   bg=self.colors['bg_light'], fg=self.colors['text_secondary'],
                                   relief=tk.FLAT, width=12, cursor='hand2', command=self.toggle_continuous_voice,
                                   activebackground=self.colors['accent_magenta'])
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=10)
        
        # Send button
        send_btn = tk.Button(input_container, text="◈ SEND", font=('Consolas', 11, 'bold'),
                            bg=self.colors['accent_magenta'], fg='#ffffff', relief=tk.FLAT,
                            width=10, cursor='hand2', command=self.send_message,
                            activebackground=self.colors['accent_purple'])
        send_btn.pack(side=tk.LEFT, ipady=10)
        
        # ===== QUICK ACTIONS =====
        actions = tk.Frame(main, bg=self.colors['bg_dark'])
        actions.pack(fill=tk.X)
        
        quick_btns = [
            ("📁 FILES", "File Explorer kholo"),
            ("🌐 BROWSER", "Web browser kholo"),
            ("💻 SYSTEM", "System info dikhao"),
            ("📸 SCREENSHOT", "Screenshot lo"),
            ("🔊 VOL+", "Volume badhao"),
            ("🔇 MUTE", "Mute karo"),
            ("🔒 LOCK", "PC lock karo"),
        ]
        
        for text, cmd in quick_btns:
            btn = tk.Button(actions, text=text, font=('Consolas', 9, 'bold'),
                           bg=self.colors['bg_light'], fg=self.colors['accent_purple'],
                           relief=tk.FLAT, padx=12, pady=6, cursor='hand2',
                           command=lambda c=cmd: self.quick_action(c),
                           activebackground=self.colors['bg_mid'])
            btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # ===== FOOTER =====
        footer = tk.Label(main, text="◈ DAXXTEAM ◈ Powered by Groq AI ◈ Llama 3.3 70B ◈ 100% FREE",
                         font=('Consolas', 9), fg=self.colors['text_secondary'], bg=self.colors['bg_dark'])
        footer.pack(pady=(15, 0))
        
        # Welcome message
        self.add_message("JEEVES", "Namaste Boss! Main JEEVES hoon, aapka personal AI assistant. Groq API key daalo aur 'Connect' karo. Key FREE mein milegi 'GET FREE KEY' se!", 'jeeves')
        
        # Start glow animation
        self.animate_icon()
    
    def animate_icon(self):
        """Animate the icon with color cycling"""
        colors = [self.colors['accent_cyan'], self.colors['accent_magenta'], 
                  self.colors['accent_purple'], self.colors['accent_green']]
        
        def cycle():
            if hasattr(self, 'icon_label'):
                current = self.icon_label.cget('fg')
                idx = colors.index(current) if current in colors else 0
                next_color = colors[(idx + 1) % len(colors)]
                self.icon_label.config(fg=next_color)
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
    
    def connect_api(self):
        api_key = self.api_key.get().strip()
        if not api_key:
            messagebox.showerror("Error", "API key daalo pehle!")
            return
        
        try:
            self.client = Groq(api_key=api_key)
            
            # Test
            self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Say 'JEEVES online'"}],
                max_tokens=10
            )
            
            self.chat_history = [{"role": "system", "content": self.system_prompt}]
            
            # Update UI
            self.status_dot.config(fg=self.colors['accent_green'])
            self.status_text.config(text="ONLINE", fg=self.colors['accent_green'])
            self.connect_btn.config(text="✓ CONNECTED", bg=self.colors['accent_green'])
            
            self.save_config()
            self.add_message("SYSTEM", "Groq AI se connect ho gaya! Ab bolo ya likho.", 'system')
            self.speak("JEEVES online ho gaya Boss! Main ready hoon aapki madad ke liye!")
            
        except Exception as e:
            self.status_dot.config(fg='#ff3333')
            self.status_text.config(text="ERROR", fg='#ff3333')
            messagebox.showerror("Error", f"Connect nahi hua: {str(e)}")
    
    def send_message(self):
        message = self.input_entry.get().strip()
        if not message:
            return
        
        if not self.client:
            messagebox.showwarning("Oops!", "Pehle API key connect karo!")
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
                max_tokens=1024,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content
            self.chat_history.append({"role": "assistant", "content": reply})
            
            # Trim history
            if len(self.chat_history) > 22:
                self.chat_history = [self.chat_history[0]] + self.chat_history[-20:]
            
            # Execute commands
            self.execute_commands(reply)
            
            # Clean display
            display = reply
            for cmd in ['CMD:OPEN_APP:', 'CMD:OPEN_URL:', 'CMD:SEARCH:', 'CMD:SYSTEM_INFO', 
                       'CMD:SCREENSHOT', 'CMD:VOLUME:', 'CMD:LOCK', 'CMD:SHUTDOWN', 'CMD:RESTART']:
                if cmd in display:
                    idx = display.find(cmd)
                    end = display.find('\n', idx) if '\n' in display[idx:] else len(display)
                    display = display[:idx] + display[end:]
            
            self.root.after(0, lambda: self.add_message("JEEVES", display.strip(), 'jeeves'))
            self.speak(display.strip())
            
        except Exception as e:
            self.root.after(0, lambda: self.add_message("SYSTEM", f"Error: {str(e)}", 'error'))
    
    def execute_commands(self, text):
        system = platform.system()
        
        if 'CMD:OPEN_APP:' in text:
            app = text.split('CMD:OPEN_APP:')[1].split('\n')[0].strip().lower()
            try:
                if system == 'Windows':
                    apps = {'chrome': 'chrome', 'firefox': 'firefox', 'edge': 'msedge',
                           'notepad': 'notepad', 'calculator': 'calc', 'explorer': 'explorer',
                           'cmd': 'cmd', 'terminal': 'wt', 'vscode': 'code', 'file explorer': 'explorer'}
                    subprocess.Popen(apps.get(app, app), shell=True)
            except Exception as e:
                self.root.after(0, lambda: self.add_message("SYSTEM", f"App nahi khula: {e}", 'error'))
        
        if 'CMD:OPEN_URL:' in text:
            url = text.split('CMD:OPEN_URL:')[1].split('\n')[0].strip()
            if not url.startswith('http'):
                url = 'https://' + url
            webbrowser.open(url)
        
        if 'CMD:SEARCH:' in text:
            query = text.split('CMD:SEARCH:')[1].split('\n')[0].strip()
            webbrowser.open(f'https://www.google.com/search?q={query}')
        
        if 'CMD:SYSTEM_INFO' in text:
            info = self.get_system_info()
            self.root.after(0, lambda: self.add_message("SYSTEM", info, 'system'))
        
        if 'CMD:SCREENSHOT' in text:
            try:
                import pyautogui
                path = Path.home() / 'Desktop' / f'screenshot_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                pyautogui.screenshot(str(path))
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Screenshot: {path}", 'system'))
            except Exception as e:
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Screenshot fail: {e}", 'error'))
        
        if 'CMD:VOLUME:' in text:
            action = text.split('CMD:VOLUME:')[1].split('\n')[0].strip().lower()
            try:
                import pyautogui
                if action == 'up':
                    pyautogui.press('volumeup', presses=5)
                elif action == 'down':
                    pyautogui.press('volumedown', presses=5)
                elif action == 'mute':
                    pyautogui.press('volumemute')
            except:
                pass
        
        if 'CMD:LOCK' in text:
            if system == 'Windows':
                os.system('rundll32.exe user32.dll,LockWorkStation')
    
    def get_system_info(self):
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return f"""◈ SYSTEM INFO ◈
━━━━━━━━━━━━━━━━━━
OS: {platform.system()} {platform.release()}
CPU: {cpu}%
RAM: {mem.percent}% ({mem.used//(1024**3)}GB / {mem.total//(1024**3)}GB)
Disk: {disk.percent}% used
━━━━━━━━━━━━━━━━━━"""
        except:
            return "System info nahi mila"
    
    def toggle_continuous_voice(self):
        """Toggle continuous listening mode"""
        if self.continuous_listen:
            self.continuous_listen = False
            self.is_listening = False
            self.voice_btn.config(text="🎤 MIC OFF", bg=self.colors['bg_light'], 
                                 fg=self.colors['text_secondary'])
            self.add_message("SYSTEM", "Mic OFF ho gaya", 'system')
        else:
            if not self.client:
                messagebox.showwarning("Oops!", "Pehle API connect karo!")
                return
            self.continuous_listen = True
            self.voice_btn.config(text="🔴 MIC ON", bg=self.colors['accent_magenta'], 
                                 fg='#ffffff')
            self.add_message("SYSTEM", "Mic ON! Ab bolo... (phir se click karke OFF karo)", 'system')
            threading.Thread(target=self.continuous_listen_loop, daemon=True).start()
    
    def continuous_listen_loop(self):
        """Continuously listen for voice commands"""
        while self.continuous_listen:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    self.root.after(0, lambda: self.add_message("SYSTEM", "🎧 Sun raha hoon...", 'system'))
                    
                    try:
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        
                        # Try Hindi first, then English
                        try:
                            text = self.recognizer.recognize_google(audio, language='hi-IN')
                        except:
                            text = self.recognizer.recognize_google(audio, language='en-IN')
                        
                        if text and self.continuous_listen:
                            self.root.after(0, lambda t=text: self.process_voice_input(t))
                            time.sleep(1)  # Small delay before next listen
                            
                    except sr.WaitTimeoutError:
                        pass  # No speech, continue listening
                    except sr.UnknownValueError:
                        pass  # Couldn't understand, continue
                        
            except Exception as e:
                if self.continuous_listen:
                    self.root.after(0, lambda: self.add_message("SYSTEM", f"Mic error: {e}", 'error'))
                time.sleep(1)
    
    def process_voice_input(self, text):
        """Process voice input"""
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, text)
        self.send_message()
    
    def speak(self, text):
        if self.tts_engine and text:
            clean = text[:500]
            for skip in ['CMD:', 'http', 'https', '━', '◈', '●']:
                clean = clean.replace(skip, '')
            threading.Thread(target=self._speak, args=(clean,), daemon=True).start()
    
    def _speak(self, text):
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except:
            pass
    
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
