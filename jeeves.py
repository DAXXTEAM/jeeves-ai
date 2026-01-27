"""
JEEVES AI - Personal PC Assistant
By DAXXTEAM

Features:
- Voice Commands (Speech to Text)
- AI Chat (Groq AI - FREE & FAST)
- System Control (Apps, Files, Commands)
- Voice Response (Text to Speech)
- Beautiful Dark UI

Requirements:
pip install groq SpeechRecognition pyttsx3 pyautogui psutil pillow

Usage:
1. Get FREE Groq API key from: https://console.groq.com/keys
2. Run: python jeeves.py
3. Enter your API key
4. Start talking to JEEVES!
"""

import os
import sys
import json
import subprocess
import webbrowser
import threading
import datetime
import platform
from pathlib import Path

# GUI
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# Check and install dependencies
def install_dependencies():
    required = {
        'groq': 'groq',
        'SpeechRecognition': 'speech_recognition',
        'pyttsx3': 'pyttsx3',
        'psutil': 'psutil',
        'pillow': 'PIL',
        'pyautogui': 'pyautogui'
    }
    for package, import_name in required.items():
        try:
            __import__(import_name.split('.')[0])
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])

install_dependencies()

from groq import Groq
import speech_recognition as sr
import pyttsx3
import psutil

class JeevesAI:
    def __init__(self, root):
        self.root = root
        self.root.title("JEEVES AI - Personal Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg='#0f172a')
        self.root.resizable(True, True)
        
        # Variables
        self.api_key = tk.StringVar()
        self.is_listening = False
        self.client = None
        self.chat_history = []
        self.tts_engine = None
        self.recognizer = sr.Recognizer()
        
        # Load saved API key
        self.config_file = Path.home() / '.jeeves_config.json'
        self.load_config()
        
        # Initialize TTS
        self.init_tts()
        
        # Create UI
        self.create_ui()
        
        # System prompt
        self.system_prompt = """You are JEEVES, an advanced AI personal assistant created by DAXXTEAM. You can:

1. SYSTEM COMMANDS (prefix with CMD:):
   - CMD:OPEN_APP:<app_name> - Open applications
   - CMD:OPEN_URL:<url> - Open websites
   - CMD:SEARCH:<query> - Google search
   - CMD:CREATE_FILE:<path>:<content> - Create files
   - CMD:READ_FILE:<path> - Read files
   - CMD:LIST_FILES:<path> - List directory
   - CMD:SYSTEM_INFO - Get system info
   - CMD:SCREENSHOT - Take screenshot
   - CMD:VOLUME:<up/down/mute> - Control volume
   - CMD:SHUTDOWN - Shutdown PC
   - CMD:RESTART - Restart PC
   - CMD:LOCK - Lock PC

2. INFORMATION:
   - Current time/date
   - Calculations
   - General knowledge
   - Coding help

3. PERSONALITY:
   - Be helpful, friendly, slightly witty
   - Call the user "Sir" or "Ma'am"
   - Be proactive in suggesting solutions

When executing commands, first explain what you're doing, then output the command.
Example: "Opening Google Chrome for you, Sir. CMD:OPEN_APP:chrome"

Always respond conversationally but be efficient. Keep responses concise."""

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
            for voice in voices:
                if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            self.tts_engine.setProperty('rate', 180)
        except Exception as e:
            print(f"TTS Error: {e}")
            self.tts_engine = None
    
    def create_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#0f172a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#0f172a')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="🤖 JEEVES AI", font=('Segoe UI', 28, 'bold'),
                              fg='#3b82f6', bg='#0f172a')
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(header_frame, text="Personal Assistant (Powered by Groq)", font=('Segoe UI', 12),
                                 fg='#64748b', bg='#0f172a')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=(12, 0))
        
        # API Key Frame
        api_frame = tk.Frame(main_frame, bg='#1e293b', padx=15, pady=15)
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(api_frame, text="Groq API Key:", font=('Segoe UI', 10),
                fg='#94a3b8', bg='#1e293b').pack(side=tk.LEFT)
        
        api_entry = tk.Entry(api_frame, textvariable=self.api_key, font=('Consolas', 10),
                            bg='#334155', fg='#f1f5f9', insertbackground='#f1f5f9',
                            relief=tk.FLAT, width=50, show='*')
        api_entry.pack(side=tk.LEFT, padx=(10, 10), ipady=5)
        
        connect_btn = tk.Button(api_frame, text="Connect", font=('Segoe UI', 10, 'bold'),
                               bg='#3b82f6', fg='white', relief=tk.FLAT, padx=20, pady=5,
                               cursor='hand2', command=self.connect_api)
        connect_btn.pack(side=tk.LEFT)
        
        get_key_btn = tk.Button(api_frame, text="Get FREE Key", font=('Segoe UI', 9),
                               bg='#1e293b', fg='#3b82f6', relief=tk.FLAT,
                               cursor='hand2', command=lambda: webbrowser.open('https://console.groq.com/keys'))
        get_key_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        self.status_label = tk.Label(api_frame, text="● Disconnected", font=('Segoe UI', 10),
                                    fg='#ef4444', bg='#1e293b')
        self.status_label.pack(side=tk.RIGHT)
        
        # Chat Frame
        chat_frame = tk.Frame(main_frame, bg='#1e293b')
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, font=('Segoe UI', 11),
                                                      bg='#1e293b', fg='#f1f5f9',
                                                      relief=tk.FLAT, wrap=tk.WORD,
                                                      padx=15, pady=15, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display.tag_config('user', foreground='#3b82f6', font=('Segoe UI', 11, 'bold'))
        self.chat_display.tag_config('jeeves', foreground='#10b981', font=('Segoe UI', 11, 'bold'))
        self.chat_display.tag_config('system', foreground='#f59e0b', font=('Segoe UI', 10, 'italic'))
        self.chat_display.tag_config('error', foreground='#ef4444')
        
        # Input Frame
        input_frame = tk.Frame(main_frame, bg='#0f172a')
        input_frame.pack(fill=tk.X)
        
        self.input_entry = tk.Entry(input_frame, font=('Segoe UI', 12),
                                   bg='#1e293b', fg='#f1f5f9', insertbackground='#f1f5f9',
                                   relief=tk.FLAT)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=12, padx=(0, 10))
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        
        self.voice_btn = tk.Button(input_frame, text="🎤", font=('Segoe UI', 16),
                                  bg='#334155', fg='#f1f5f9', relief=tk.FLAT,
                                  width=3, cursor='hand2', command=self.toggle_voice)
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        send_btn = tk.Button(input_frame, text="Send", font=('Segoe UI', 11, 'bold'),
                            bg='#3b82f6', fg='white', relief=tk.FLAT, padx=25, pady=10,
                            cursor='hand2', command=self.send_message)
        send_btn.pack(side=tk.LEFT)
        
        # Quick Actions Frame
        actions_frame = tk.Frame(main_frame, bg='#0f172a')
        actions_frame.pack(fill=tk.X, pady=(15, 0))
        
        quick_actions = [
            ("📁 Explorer", "Open File Explorer"),
            ("🌐 Browser", "Open web browser"),
            ("💻 System", "Show system information"),
            ("📸 Screenshot", "Take a screenshot"),
            ("🔊 Vol+", "Increase volume"),
            ("🔇 Mute", "Mute audio"),
        ]
        
        for text, command in quick_actions:
            btn = tk.Button(actions_frame, text=text, font=('Segoe UI', 9),
                           bg='#334155', fg='#f1f5f9', relief=tk.FLAT, padx=10, pady=5,
                           cursor='hand2', command=lambda c=command: self.quick_action(c))
            btn.pack(side=tk.LEFT, padx=(0, 8))
        
        footer = tk.Label(main_frame, text="Made with ❤️ by DAXXTEAM | Powered by Groq (FREE & FAST)",
                         font=('Segoe UI', 9), fg='#64748b', bg='#0f172a')
        footer.pack(pady=(15, 0))
        
        self.add_message("JEEVES", "Good day! I'm JEEVES, your personal AI assistant. Get your FREE Groq API key by clicking 'Get FREE Key'. Groq is super fast and completely free!", 'jeeves')
    
    def add_message(self, sender, message, tag='user'):
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"\n[{timestamp}] {sender}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def connect_api(self):
        api_key = self.api_key.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Groq API key")
            return
        
        try:
            self.client = Groq(api_key=api_key)
            
            # Test connection
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Say 'JEEVES online' in 2 words"}],
                max_tokens=10
            )
            
            self.chat_history = [{"role": "system", "content": self.system_prompt}]
            
            self.status_label.config(text="● Connected", fg='#10b981')
            self.save_config()
            self.add_message("SYSTEM", "Connected to Groq AI (Llama 3.3 70B)!", 'system')
            self.speak("JEEVES online and ready to assist, Sir!")
            
        except Exception as e:
            self.status_label.config(text="● Error", fg='#ef4444')
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
    
    def send_message(self):
        message = self.input_entry.get().strip()
        if not message:
            return
        
        if not self.client:
            messagebox.showwarning("Not Connected", "Please connect your API key first")
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
            
            if len(self.chat_history) > 22:
                self.chat_history = [self.chat_history[0]] + self.chat_history[-20:]
            
            self.execute_commands(reply)
            
            display_reply = reply
            for cmd in ['CMD:OPEN_APP:', 'CMD:OPEN_URL:', 'CMD:SEARCH:', 'CMD:CREATE_FILE:',
                       'CMD:READ_FILE:', 'CMD:LIST_FILES:', 'CMD:SYSTEM_INFO', 'CMD:SCREENSHOT',
                       'CMD:VOLUME:', 'CMD:SHUTDOWN', 'CMD:RESTART', 'CMD:LOCK']:
                if cmd in display_reply:
                    idx = display_reply.find(cmd)
                    end_idx = display_reply.find('\n', idx) if '\n' in display_reply[idx:] else len(display_reply)
                    display_reply = display_reply[:idx] + display_reply[end_idx:]
            
            self.root.after(0, lambda: self.add_message("JEEVES", display_reply.strip(), 'jeeves'))
            self.speak(display_reply.strip())
            
        except Exception as e:
            self.root.after(0, lambda: self.add_message("SYSTEM", f"Error: {str(e)}", 'error'))
    
    def execute_commands(self, text):
        system = platform.system()
        
        if 'CMD:OPEN_APP:' in text:
            app = text.split('CMD:OPEN_APP:')[1].split('\n')[0].strip().lower()
            try:
                if system == 'Windows':
                    apps = {
                        'chrome': 'chrome', 'firefox': 'firefox', 'edge': 'msedge',
                        'notepad': 'notepad', 'calculator': 'calc', 'explorer': 'explorer',
                        'cmd': 'cmd', 'terminal': 'cmd', 'vscode': 'code', 'word': 'winword',
                        'excel': 'excel', 'powerpoint': 'powerpnt', 'spotify': 'spotify',
                        'file explorer': 'explorer', 'files': 'explorer',
                    }
                    subprocess.Popen(apps.get(app, app), shell=True)
                elif system == 'Darwin':
                    subprocess.Popen(['open', '-a', app])
                else:
                    subprocess.Popen([app])
            except Exception as e:
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Couldn't open {app}: {e}", 'error'))
        
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
                screenshot_path = Path.home() / 'Desktop' / f'screenshot_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                pyautogui.screenshot(str(screenshot_path))
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Screenshot saved: {screenshot_path}", 'system'))
            except Exception as e:
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Screenshot failed: {e}", 'error'))
        
        if 'CMD:VOLUME:' in text:
            action = text.split('CMD:VOLUME:')[1].split('\n')[0].strip().lower()
            try:
                if system == 'Windows':
                    import pyautogui
                    if action == 'up':
                        pyautogui.press('volumeup', presses=5)
                    elif action == 'down':
                        pyautogui.press('volumedown', presses=5)
                    elif action == 'mute':
                        pyautogui.press('volumemute')
            except:
                pass
        
        if 'CMD:CREATE_FILE:' in text:
            parts = text.split('CMD:CREATE_FILE:')[1].split('\n')[0].strip()
            if ':' in parts:
                path, content = parts.split(':', 1)
                try:
                    Path(path).write_text(content)
                    self.root.after(0, lambda: self.add_message("SYSTEM", f"File created: {path}", 'system'))
                except Exception as e:
                    self.root.after(0, lambda: self.add_message("SYSTEM", f"Error: {e}", 'error'))
        
        if 'CMD:READ_FILE:' in text:
            path = text.split('CMD:READ_FILE:')[1].split('\n')[0].strip()
            try:
                content = Path(path).read_text()[:1000]
                self.root.after(0, lambda: self.add_message("SYSTEM", f"File content:\n{content}", 'system'))
            except Exception as e:
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Error: {e}", 'error'))
        
        if 'CMD:LIST_FILES:' in text:
            path = text.split('CMD:LIST_FILES:')[1].split('\n')[0].strip()
            try:
                files = list(Path(path).iterdir())[:20]
                file_list = '\n'.join([f.name for f in files])
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Files:\n{file_list}", 'system'))
            except Exception as e:
                self.root.after(0, lambda: self.add_message("SYSTEM", f"Error: {e}", 'error'))
        
        if 'CMD:SHUTDOWN' in text:
            if messagebox.askyesno("Confirm", "Are you sure you want to shutdown?"):
                os.system('shutdown /s /t 5' if system == 'Windows' else 'shutdown -h now')
        
        if 'CMD:RESTART' in text:
            if messagebox.askyesno("Confirm", "Are you sure you want to restart?"):
                os.system('shutdown /r /t 5' if system == 'Windows' else 'shutdown -r now')
        
        if 'CMD:LOCK' in text:
            if system == 'Windows':
                os.system('rundll32.exe user32.dll,LockWorkStation')
    
    def get_system_info(self):
        try:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return f"""System Information:
━━━━━━━━━━━━━━━━━━━━━━━━
• OS: {platform.system()} {platform.release()}
• CPU Usage: {cpu}%
• RAM: {memory.percent}% ({memory.used // (1024**3):.1f} GB / {memory.total // (1024**3):.1f} GB)
• Disk: {disk.percent}% ({disk.used // (1024**3):.1f} GB / {disk.total // (1024**3):.1f} GB)
• Python: {platform.python_version()}
━━━━━━━━━━━━━━━━━━━━━━━━"""
        except:
            return "Could not retrieve system info"
    
    def toggle_voice(self):
        if self.is_listening:
            self.is_listening = False
            self.voice_btn.config(bg='#334155', text='🎤')
        else:
            self.is_listening = True
            self.voice_btn.config(bg='#ef4444', text='🔴')
            threading.Thread(target=self.listen_voice, daemon=True).start()
    
    def listen_voice(self):
        try:
            with sr.Microphone() as source:
                self.root.after(0, lambda: self.add_message("SYSTEM", "Listening...", 'system'))
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio)
            self.root.after(0, lambda: self.input_entry.insert(0, text))
            self.root.after(100, self.send_message)
            
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.add_message("SYSTEM", "No speech detected", 'system'))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.add_message("SYSTEM", "Could not understand audio", 'system'))
        except Exception as e:
            self.root.after(0, lambda: self.add_message("SYSTEM", f"Voice error: {e}", 'error'))
        finally:
            self.is_listening = False
            self.root.after(0, lambda: self.voice_btn.config(bg='#334155', text='🎤'))
    
    def speak(self, text):
        if self.tts_engine:
            clean_text = text[:500]
            for cmd in ['CMD:', 'http', 'https', '━', '•']:
                clean_text = clean_text.replace(cmd, '')
            threading.Thread(target=self._speak_thread, args=(clean_text,), daemon=True).start()
    
    def _speak_thread(self, text):
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
