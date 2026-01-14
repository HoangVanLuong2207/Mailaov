import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import pyperclip
import pyautogui
import time
import json
import os
import requests
import re
import threading
from urllib.parse import quote
import subprocess

class AccountManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Account Manager (user|pass|mail)")
        self.root.geometry("750x700")
        self.root.configure(bg="#1e1e2e")
        self.root.attributes('-topmost', True)  # Always on top

        # UI Styling
        self.primary_color = "#89b4fa"
        self.bg_color = "#1e1e2e"
        self.surface_color = "#313244"
        self.text_color = "#cdd6f4"
        self.accent_color = "#f38ba8"
        self.green_color = "#a6e3a1"
        self.yellow_color = "#f9e2af"
        self.purple_color = "#cba6f7"

        # File storage paths
        self.combos_file = os.path.join(os.path.dirname(__file__), "combos.json")
        self.accounts_file = os.path.join(os.path.dirname(__file__), "accounts.txt")
        self.combos = self.load_combos()
        self.combo_buttons = []
        
        # Store last fetched code to detect duplicates
        self.last_fetched_code = None
        self.max_retry_attempts = 5
        self.retry_delay = 1.5  # seconds
        
        # URL input variable
        self.url_var = None  # Will be set in setup_ui
        
        # Available actions for combo
        self.available_actions = {
            "Dán User": self.paste_user_no_switch,
            "Dán Pass": self.paste_pass_no_switch,
            "Dán Mail": self.paste_mail_no_switch,
            "Dán Nội Dung": self.paste_custom_no_switch,
            "Tab": self.tab_no_switch,
            "Enter": self.enter_no_switch,
            "Lấy Code": self.fetch_code_no_switch,
            "Vào URL": self.goto_url_no_switch,
            "Đợi 0.1s": lambda: time.sleep(0.1),
            "Đợi 0.5s": lambda: time.sleep(0.5),
            "Đợi 1s": lambda: time.sleep(1),
            "Click": lambda: pyautogui.click(),
            "Đóng & Mở Mới": self.close_and_new_no_switch,
        }

        # Initialize UI Components
        self.setup_ui()
        
        # Load saved accounts
        self.load_accounts()
        
        # Save accounts on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(header_frame, text="Account List Manager", font=("Segoe UI", 16, "bold"), 
                              fg=self.primary_color, bg=self.bg_color)
        title_label.pack()

        # Action Buttons Frame (Ctrl+V simulations) - AT TOP
        action_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        action_frame.pack(fill=tk.X)
        
        action_label = tk.Label(action_frame, text="Ctrl+V Actions:", font=("Segoe UI", 10),
                               fg=self.text_color, bg=self.bg_color)
        action_label.pack(side=tk.LEFT, padx=(20, 10))

        self.btn_paste_user = tk.Button(action_frame, text="Dán User", font=("Segoe UI", 10, "bold"),
                                        bg=self.green_color, fg=self.bg_color, activebackground="#b5e8b5",
                                        padx=15, pady=8, command=self.paste_user, borderwidth=0)
        self.btn_paste_user.pack(side=tk.LEFT, padx=5)

        self.btn_paste_pass = tk.Button(action_frame, text="Dán Pass", font=("Segoe UI", 10, "bold"),
                                        bg=self.yellow_color, fg=self.bg_color, activebackground="#faecc5",
                                        padx=15, pady=8, command=self.paste_pass, borderwidth=0)
        self.btn_paste_pass.pack(side=tk.LEFT, padx=5)

        self.btn_paste_mail = tk.Button(action_frame, text="Dán Mail", font=("Segoe UI", 10, "bold"),
                                        bg=self.purple_color, fg=self.bg_color, activebackground="#d9c4f9",
                                        padx=15, pady=8, command=self.paste_mail, borderwidth=0)
        self.btn_paste_mail.pack(side=tk.LEFT, padx=5)

        self.btn_paste_only = tk.Button(action_frame, text="Dán", font=("Segoe UI", 10, "bold"),
                                        bg="#94e2d5", fg=self.bg_color, activebackground="#b5ece5",
                                        padx=15, pady=8, command=self.paste_only, borderwidth=0)
        self.btn_paste_only.pack(side=tk.LEFT, padx=5)

        self.btn_delete_line = tk.Button(action_frame, text="Xoá Dòng Đầu", font=("Segoe UI", 10, "bold"),
                                         bg=self.accent_color, fg=self.bg_color, activebackground="#f5c2e7",
                                         padx=15, pady=8, command=self.delete_first_line_and_action, borderwidth=0)
        self.btn_delete_line.pack(side=tk.LEFT, padx=5)

        # List Management Frame - SECOND ROW
        list_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        list_frame.pack(fill=tk.X)

        # Custom content entry for "Dán Nội Dung"
        self.custom_content_var = tk.StringVar(value="")
        self.custom_content_entry = tk.Entry(list_frame, textvariable=self.custom_content_var,
                                             font=("Consolas", 10), bg=self.surface_color, fg=self.text_color,
                                             insertbackground=self.text_color, width=15, borderwidth=0)
        self.custom_content_entry.pack(side=tk.LEFT, padx=5)
        self.custom_content_entry.insert(0, "Nhập nội dung...")

        self.btn_paste_custom = tk.Button(list_frame, text="Dán Nội Dung", font=("Segoe UI", 10, "bold"),
                                  bg=self.surface_color, fg=self.text_color, activebackground="#45475a",
                                  padx=20, pady=8, command=self.paste_custom_content, borderwidth=0)
        self.btn_paste_custom.pack(side=tk.LEFT, padx=5)

        self.btn_tab = tk.Button(list_frame, text="Tab", font=("Segoe UI", 10, "bold"),
                                 bg="#fab387", fg=self.bg_color, activebackground="#fbc4a4",
                                 padx=20, pady=8, command=self.tab_action, borderwidth=0)
        self.btn_tab.pack(side=tk.LEFT, padx=5)

        self.btn_enter = tk.Button(list_frame, text="Enter", font=("Segoe UI", 10, "bold"),
                                   bg="#f2cdcd", fg=self.bg_color, activebackground="#f5e0dc",
                                   padx=20, pady=8, command=self.enter_action, borderwidth=0)
        self.btn_enter.pack(side=tk.LEFT, padx=5)

        self.btn_fetch_code = tk.Button(list_frame, text="Lấy Code", font=("Segoe UI", 10, "bold"),
                                   bg="#f38ba8", fg=self.bg_color, activebackground="#f5a0b8",
                                   padx=20, pady=8, command=self.fetch_mail_code, borderwidth=0)
        self.btn_fetch_code.pack(side=tk.LEFT, padx=5)

        self.btn_close_new = tk.Button(list_frame, text="Đóng & Mở Mới", font=("Segoe UI", 10, "bold"),
                                       bg="#eba0ac", fg=self.bg_color, activebackground="#f5c2c7",
                                       padx=15, pady=8, command=self.close_and_new_action, borderwidth=0)
        self.btn_close_new.pack(side=tk.LEFT, padx=5)

        # ROW 2.25: URL Navigation
        url_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        url_frame.pack(fill=tk.X)
        
        url_label = tk.Label(url_frame, text="URL:", font=("Segoe UI", 10),
                             fg=self.text_color, bg=self.bg_color)
        url_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.url_var = tk.StringVar(value="")
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var,
                                  font=("Consolas", 10), bg=self.surface_color, fg=self.text_color,
                                  insertbackground=self.text_color, width=40, borderwidth=0)
        self.url_entry.pack(side=tk.LEFT, padx=5)
        self.url_entry.insert(0, "https://")
        
        self.btn_goto_url = tk.Button(url_frame, text="Vào URL", font=("Segoe UI", 10, "bold"),
                                      bg="#89b4fa", fg=self.bg_color, activebackground="#a6c8ff",
                                      padx=15, pady=8, command=self.goto_url_action, borderwidth=0)
        self.btn_goto_url.pack(side=tk.LEFT, padx=5)

        # ROW 2.5: Proxy Chrome Launcher
        proxy_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        proxy_frame.pack(fill=tk.X)
        
        proxy_label = tk.Label(proxy_frame, text="Proxy:", font=("Segoe UI", 10),
                               fg=self.text_color, bg=self.bg_color)
        proxy_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.proxy_var = tk.StringVar(value="")
        self.proxy_entry = tk.Entry(proxy_frame, textvariable=self.proxy_var,
                                    font=("Consolas", 10), bg=self.surface_color, fg=self.text_color,
                                    insertbackground=self.text_color, width=25, borderwidth=0)
        self.proxy_entry.pack(side=tk.LEFT, padx=5)
        self.proxy_entry.insert(0, "ip:port")
        
        self.btn_open_chrome = tk.Button(proxy_frame, text="Mở Chrome + Proxy", font=("Segoe UI", 10, "bold"),
                                         bg="#74c7ec", fg=self.bg_color, activebackground="#89dceb",
                                         padx=15, pady=8, command=self.open_chrome_with_proxy, borderwidth=0)
        self.btn_open_chrome.pack(side=tk.LEFT, padx=5)

        # ROW 3: Combo Actions
        self.combo_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        self.combo_frame.pack(fill=tk.X)
        
        combo_label = tk.Label(self.combo_frame, text="Combos:", font=("Segoe UI", 10),
                               fg=self.text_color, bg=self.bg_color)
        combo_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.btn_add_combo = tk.Button(self.combo_frame, text="➕ Tạo Combo", font=("Segoe UI", 10, "bold"),
                                       bg="#b4befe", fg=self.bg_color, activebackground="#c8d0ff",
                                       padx=15, pady=8, command=self.create_combo_dialog, borderwidth=0)
        self.btn_add_combo.pack(side=tk.LEFT, padx=5)
        
        # Render existing combos
        self.render_combo_buttons()

        # Status Bar - BELOW BUTTONS
        self.status_var = tk.StringVar(value="Tổng cộng: 0 dòng | Dòng hiện tại: -")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg=self.surface_color, 
                             fg=self.text_color, anchor=tk.W, padx=20, pady=8, font=("Consolas", 10))
        status_bar.pack(fill=tk.X, padx=20, pady=(5, 0))

        # Text Area - AT BOTTOM, takes remaining space
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.NONE, font=("Consolas", 11),
                                                 bg=self.surface_color, fg=self.text_color,
                                                 insertbackground=self.text_color, borderwidth=0)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        # Update count on change
        self.text_area.bind('<<Modified>>', self.on_text_modified)

    def get_first_line_parts(self):
        """Get user, pass, mail from the first line"""
        first_line = self.text_area.get("1.0", "1.end").strip()
        if not first_line:
            return None, None, None
        parts = first_line.split("|")
        user = parts[0] if len(parts) > 0 else ""
        password = parts[1] if len(parts) > 1 else ""
        mail = parts[2] if len(parts) > 2 else ""
        return user, password, mail

    def paste_user(self):
        """Copy user to clipboard and simulate Ctrl+V"""
        user, _, _ = self.get_first_line_parts()
        if user:
            pyperclip.copy(user)
            self.root.after(30, self._simulate_paste)
            self.status_var.set(f"Đã copy User: {user}")
        else:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu user!")

    def paste_pass(self):
        """Copy password to clipboard and simulate Ctrl+V"""
        _, password, _ = self.get_first_line_parts()
        if password:
            pyperclip.copy(password)
            self.root.after(30, self._simulate_paste)
            self.status_var.set(f"Đã copy Pass: {password}")
        else:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu password!")

    def paste_mail(self):
        """Copy mail to clipboard and simulate Ctrl+V"""
        _, _, mail = self.get_first_line_parts()
        if mail:
            pyperclip.copy(mail)
            self.root.after(30, self._simulate_paste)
            self.status_var.set(f"Đã copy Mail: {mail}")
        else:
            self.status_var.set("Không có mail - bỏ qua")

    def _simulate_paste(self):
        """Alt+Tab to previous window, clear and paste, then Alt+Tab back"""
        # Alt+Tab to switch to previous window
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.025)  # Brief wait
        # Clear and paste
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.01)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.015)
        # Alt+Tab back to this window
        pyautogui.hotkey('alt', 'tab')

    def paste_only(self):
        """Alt+Tab and Ctrl+V only (no clear)"""
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.025)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.015)
        pyautogui.hotkey('alt', 'tab')
        self.status_var.set("Đã dán (Ctrl+V)!")

    def delete_first_line_and_action(self):
        """Delete the first line from the list with confirmation"""
        first_line = self.text_area.get("1.0", "1.end").strip()
        if first_line:
            if messagebox.askyesno("Xác nhận", f"Xoá dòng:\n{first_line[:50]}...?" if len(first_line) > 50 else f"Xoá dòng:\n{first_line}?"):
                self.text_area.delete("1.0", "2.0")
                self.update_count()
                self.status_var.set("Đã xoá dòng đầu tiên!")
        else:
            messagebox.showinfo("Thông báo", "Danh sách đang trống.")

    def paste_list(self):
        """Paste list from clipboard"""
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content:
                current_text = self.text_area.get("1.0", tk.END).strip()
                if current_text:
                    self.text_area.insert(tk.END, "\n" + clipboard_content)
                else:
                    self.text_area.insert("1.0", clipboard_content)
                self.update_count()
        except tk.TclError:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy dữ liệu trong clipboard.")

    def paste_custom_content(self):
        """Copy custom content to clipboard and simulate Ctrl+V"""
        custom_content = self.custom_content_var.get().strip()
        if custom_content and custom_content != "Nhập nội dung...":
            pyperclip.copy(custom_content)
            self.root.after(30, self._simulate_paste)
            self.status_var.set(f"Đã dán nội dung: {custom_content}")
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập nội dung cần dán!")

    def tab_action(self):
        """Alt+Tab to switch window, then press Tab key"""
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.025)
        pyautogui.press('tab')
        time.sleep(0.015)
        pyautogui.hotkey('alt', 'tab')
        self.status_var.set("Đã Tab sang ô tiếp theo!")

    def enter_action(self):
        """Alt+Tab to switch window, then press Enter key"""
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.025)
        pyautogui.press('enter')
        time.sleep(0.015)
        pyautogui.hotkey('alt', 'tab')
        self.status_var.set("Đã Enter!")

    def close_and_new_action(self):
        """Alt+Tab -> Alt+F4 -> Ctrl+Shift+N -> Go to Garena"""
        url = "https://account.garena.com/"
        pyperclip.copy(url)
        
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.05)
        pyautogui.hotkey('alt', 'F4')
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'shift', 'n')
        time.sleep(0.3)  # Wait for new window to open
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.03)
        pyautogui.press('enter')
        self.status_var.set("Đã đóng & mở Garena!")

    def open_chrome_with_proxy(self):
        """Open Chrome browser with HTTP proxy"""
        proxy = self.proxy_var.get().strip()
        if not proxy or proxy == "ip:port":
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập proxy (ví dụ: 192.168.1.1:8080)")
            return
        
        # Common Chrome paths on Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if not chrome_path:
            messagebox.showerror("Lỗi", "Không tìm thấy Chrome! Vui lòng cài đặt Chrome.")
            return
        
        try:
            # Clean proxy format - remove any protocol prefix
            clean_proxy = proxy.replace("http://", "").replace("https://", "").replace("socks5://", "")
            
            # Launch Chrome with SOCKS5 proxy and incognito mode
            cmd = [
                chrome_path,
                f"--proxy-server=socks5://{clean_proxy}",
                "--incognito",
                "--ignore-certificate-errors",
                "https://account.garena.com/"
            ]
            subprocess.Popen(cmd)
            self.status_var.set(f"Đã mở Chrome với proxy: {clean_proxy}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở Chrome: {str(e)}")

    def f6_url_action(self):
        """Alt+Tab -> F6 -> Paste URL -> Enter"""
        url = "https://account.garena.com/security/email/save"
        pyperclip.copy(url)
        
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.05)
        pyautogui.press('f6')
        time.sleep(0.03)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.03)
        pyautogui.press('enter')
        time.sleep(0.03)
        pyautogui.hotkey('alt', 'tab')
        self.status_var.set("Đã F6 + Enter URL!")

    def verify_mail_action(self):
        """Alt+Tab -> F6 -> Paste verify email URL -> Enter"""
        url = "https://account.garena.com/security/verify_email/apply"
        pyperclip.copy(url)
        
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.05)
        pyautogui.press('f6')
        time.sleep(0.03)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.03)
        pyautogui.press('enter')
        time.sleep(0.03)
        pyautogui.hotkey('alt', 'tab')
        self.status_var.set("Đã F6 + Enter URL xác thực!")

    def fetch_mail_code(self):
        """Fetch verification code from mail API and paste it"""
        _, _, mail_user = self.get_first_line_parts()
        if not mail_user:
            self.status_var.set("Không có mail để lấy code!")
            return
        
        # Extract username from email (remove @domain if present)
        if '@' in mail_user:
            username = mail_user.split('@')[0]
        else:
            username = mail_user
        
        email = f"{username}@batdongsanvgp.com"
        print(f"[DEBUG] mail_user = '{mail_user}', username = '{username}'")  # Debug
        self.status_var.set(f"Đang lấy code từ {email}...")
        self.root.update()
        
        # Run in thread to avoid blocking UI
        def fetch_thread():
            attempt = 0
            while attempt < self.max_retry_attempts:
                attempt += 1
                try:
                    # Call via local proxy (same as index.html)
                    api_url = f"http://localhost:3000/api/get-code?username={username.strip()}"
                    print(f"[DEBUG] Attempt {attempt}: Calling: {api_url}")  # Debug log
                    response = requests.get(api_url, timeout=10)
                    
                    if response.status_code != 200:
                        self.root.after(0, lambda: self.status_var.set(f"Lỗi HTTP {response.status_code} - Chạy node server.js chưa?"))
                        return
                    
                    result = response.json()
                    
                    if not result.get('ok'):
                        self.root.after(0, lambda: self.status_var.set(f"API lỗi: {result.get('error', 'Unknown')}"))
                        return
                    
                    data = result.get('raw', [])
                    
                    # Parse code from response (same logic as index.html)
                    code = None
                    if isinstance(data, list) and len(data) > 0 and 'body' in data[0]:
                        body = data[0]['body']
                        
                        # Try pattern 1: <b>12345678</b>
                        match = re.search(r'<b[^>]>(\d{8})</b>', body)
                        if match:
                            code = match.group(1)
                        
                        # Try pattern 2: **12345678**
                        if not code:
                            match = re.search(r'\*\*(\d{8})\*\*', body)
                            if match:
                                code = match.group(1)
                        
                        # Try pattern 3: any 8 digits
                        if not code:
                            match = re.search(r'\b(\d{8})\b', body)
                            if match:
                                code = match.group(1)
                    
                    if code:
                        # Check if code is same as last fetched
                        if code == self.last_fetched_code:
                            if attempt < self.max_retry_attempts:
                                self.root.after(0, lambda a=attempt: self.status_var.set(f"Mã trùng, thử lại lần {a+1}/{self.max_retry_attempts}..."))
                                time.sleep(self.retry_delay)
                                continue  # Retry
                            else:
                                # Max retries reached, still use the code but warn
                                self.root.after(0, lambda c=code: self.status_var.set(f"⚠ Vẫn mã cũ sau {self.max_retry_attempts} lần: {c}"))
                                return
                        
                        # New code found!
                        self.last_fetched_code = code
                        pyperclip.copy(code)
                        self.root.after(0, lambda c=code: self._paste_code_to_window(c))
                        return
                    else:
                        self.root.after(0, lambda: self.status_var.set("Không tìm thấy mã 8 số!"))
                        return
                        
                except requests.exceptions.Timeout:
                    self.root.after(0, lambda: self.status_var.set("Timeout - API không phản hồi!"))
                    return
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set(f"Lỗi: {str(e)[:30]}"))
                    return
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def _paste_code_to_window(self, code):
        """Switch to other window and paste code"""
        self.status_var.set(f"Đã lấy code: {code} - Đang dán...")
        self.root.update()
        
        # Alt+Tab to switch window
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.05)
        # Clear and paste
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.02)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.03)
        # Switch back
        pyautogui.hotkey('alt', 'tab')
        
        self.status_var.set(f"✓ Đã dán code: {code}")

    def on_text_modified(self, event=None):
        if self.text_area.edit_modified():
            self.update_count()
            self.text_area.edit_modified(False)

    def update_count(self):
        content = self.text_area.get("1.0", tk.END).strip()
        lines = [line for line in content.split("\n") if line.strip()]
        first_line_preview = lines[0][:30] + "..." if lines and len(lines[0]) > 30 else (lines[0] if lines else "-")
        self.status_var.set(f"Tổng cộng: {len(lines)} dòng | Dòng đầu: {first_line_preview}")

    # ============ ACCOUNT PERSISTENCE ============
    
    def load_accounts(self):
        """Load accounts from file on startup"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        self.text_area.insert("1.0", content)
                        self.update_count()
            except Exception as e:
                print(f"Error loading accounts: {e}")
    
    def save_accounts(self):
        """Save accounts to file"""
        content = self.text_area.get("1.0", tk.END).strip()
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def on_close(self):
        """Save accounts before closing the app"""
        self.save_accounts()
        self.root.destroy()

    # ============ COMBO METHODS ============
    
    def load_combos(self):
        """Load combos from JSON file"""
        if os.path.exists(self.combos_file):
            try:
                with open(self.combos_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_combos(self):
        """Save combos to JSON file"""
        with open(self.combos_file, 'w', encoding='utf-8') as f:
            json.dump(self.combos, f, ensure_ascii=False, indent=2)
    
    def render_combo_buttons(self):
        """Render combo buttons based on saved combos"""
        # Clear existing combo buttons
        for btn in self.combo_buttons:
            btn.destroy()
        self.combo_buttons.clear()
        
        # Create buttons for each combo
        colors = ["#f5c2e7", "#94e2d5", "#fab387", "#a6e3a1", "#89dceb", "#cba6f7"]
        for i, (combo_name, actions) in enumerate(self.combos.items()):
            color = colors[i % len(colors)]
            btn = tk.Button(self.combo_frame, text=f"▶ {combo_name}", font=("Segoe UI", 9, "bold"),
                           bg=color, fg=self.bg_color, activebackground="#ffffff",
                           padx=10, pady=6, borderwidth=0,
                           command=lambda n=combo_name: self.run_combo(n))
            btn.pack(side=tk.LEFT, padx=3)
            
            # Right-click to show context menu (Edit/Delete)
            btn.bind("<Button-3>", lambda e, n=combo_name: self.show_combo_menu(e, n))
            self.combo_buttons.append(btn)
    
    def create_combo_dialog(self):
        """Open dialog to create a new combo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Tạo Combo Mới")
        dialog.geometry("500x550")
        dialog.configure(bg=self.bg_color)
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        
        # Combo name
        tk.Label(dialog, text="Tên Combo:", font=("Segoe UI", 11, "bold"),
                bg=self.bg_color, fg=self.text_color).pack(pady=(15, 5))
        
        name_entry = tk.Entry(dialog, font=("Consolas", 11), bg=self.surface_color,
                             fg=self.text_color, insertbackground=self.text_color, width=30)
        name_entry.pack(pady=5)
        
        # Actions list
        tk.Label(dialog, text="Danh sách Actions (chọn từ bên trái, thêm vào bên phải):", 
                font=("Segoe UI", 10), bg=self.bg_color, fg=self.text_color).pack(pady=(15, 5))
        
        list_frame = tk.Frame(dialog, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Available actions listbox
        avail_frame = tk.Frame(list_frame, bg=self.bg_color)
        avail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(avail_frame, text="Có sẵn:", font=("Segoe UI", 9),
                bg=self.bg_color, fg=self.text_color).pack()
        
        avail_listbox = tk.Listbox(avail_frame, font=("Consolas", 10), bg=self.surface_color,
                                   fg=self.text_color, selectbackground=self.primary_color, height=12)
        avail_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        for action_name in self.available_actions.keys():
            avail_listbox.insert(tk.END, action_name)
        
        # Buttons in middle
        btn_frame = tk.Frame(list_frame, bg=self.bg_color)
        btn_frame.pack(side=tk.LEFT, padx=10)
        
        selected_actions = []
        
        def add_action():
            selection = avail_listbox.curselection()
            if selection:
                action = avail_listbox.get(selection[0])
                selected_actions.append(action)
                update_selected_list()
        
        def remove_action():
            selection = selected_listbox.curselection()
            if selection:
                del selected_actions[selection[0]]
                update_selected_list()
        
        def move_up():
            selection = selected_listbox.curselection()
            if selection and selection[0] > 0:
                idx = selection[0]
                selected_actions[idx], selected_actions[idx-1] = selected_actions[idx-1], selected_actions[idx]
                update_selected_list()
                selected_listbox.selection_set(idx-1)
        
        def move_down():
            selection = selected_listbox.curselection()
            if selection and selection[0] < len(selected_actions) - 1:
                idx = selection[0]
                selected_actions[idx], selected_actions[idx+1] = selected_actions[idx+1], selected_actions[idx]
                update_selected_list()
                selected_listbox.selection_set(idx+1)
        
        def update_selected_list():
            selected_listbox.delete(0, tk.END)
            for i, act in enumerate(selected_actions):
                selected_listbox.insert(tk.END, f"{i+1}. {act}")
        
        tk.Button(btn_frame, text="→", font=("Segoe UI", 12, "bold"), bg=self.green_color,
                 fg=self.bg_color, command=add_action, width=3).pack(pady=5)
        tk.Button(btn_frame, text="←", font=("Segoe UI", 12, "bold"), bg=self.accent_color,
                 fg=self.bg_color, command=remove_action, width=3).pack(pady=5)
        tk.Button(btn_frame, text="↑", font=("Segoe UI", 12, "bold"), bg=self.yellow_color,
                 fg=self.bg_color, command=move_up, width=3).pack(pady=5)
        tk.Button(btn_frame, text="↓", font=("Segoe UI", 12, "bold"), bg=self.yellow_color,
                 fg=self.bg_color, command=move_down, width=3).pack(pady=5)
        
        # Selected actions listbox
        selected_frame = tk.Frame(list_frame, bg=self.bg_color)
        selected_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(selected_frame, text="Đã chọn (theo thứ tự):", font=("Segoe UI", 9),
                bg=self.bg_color, fg=self.text_color).pack()
        
        selected_listbox = tk.Listbox(selected_frame, font=("Consolas", 10), bg=self.surface_color,
                                      fg=self.text_color, selectbackground=self.primary_color, height=12)
        selected_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Save button
        def save_combo():
            combo_name = name_entry.get().strip()
            if not combo_name:
                messagebox.showwarning("Lỗi", "Vui lòng nhập tên combo!")
                return
            if not selected_actions:
                messagebox.showwarning("Lỗi", "Vui lòng chọn ít nhất 1 action!")
                return
            
            self.combos[combo_name] = selected_actions.copy()
            self.save_combos()
            self.render_combo_buttons()
            dialog.destroy()
            self.status_var.set(f"Đã tạo combo: {combo_name}")
        
        tk.Button(dialog, text="💾 Lưu Combo", font=("Segoe UI", 11, "bold"),
                 bg=self.green_color, fg=self.bg_color, activebackground="#b5e8b5",
                 padx=20, pady=10, command=save_combo, borderwidth=0).pack(pady=15)
    
    def run_combo(self, combo_name):
        """Execute a combo sequence"""
        if combo_name not in self.combos:
            return
        
        actions = self.combos[combo_name]
        self.status_var.set(f"Đang chạy combo: {combo_name}...")
        self.root.update()
        
        # Switch to other window first
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.05)
        
        # Execute each action
        for action_name in actions:
            if action_name in self.available_actions:
                try:
                    self.available_actions[action_name]()
                    time.sleep(0.025)  # Small delay between actions
                except Exception as e:
                    print(f"Error in action {action_name}: {e}")
        
        # Switch back 
        pyautogui.hotkey('alt', 'tab')
        self.status_var.set(f"Hoàn thành combo: {combo_name}")
    
    def show_combo_menu(self, event, combo_name):
        """Show context menu for combo (Edit/Delete)"""
        menu = tk.Menu(self.root, tearoff=0, bg=self.surface_color, fg=self.text_color,
                      activebackground=self.primary_color, activeforeground=self.bg_color)
        menu.add_command(label="✏️ Sửa Combo", command=lambda: self.edit_combo_dialog(combo_name))
        menu.add_separator()
        menu.add_command(label="🗑️ Xoá Combo", command=lambda: self.delete_combo_dialog(combo_name))
        menu.tk_popup(event.x_root, event.y_root)
    
    def delete_combo_dialog(self, combo_name):
        """Delete a combo with confirmation"""
        if messagebox.askyesno("Xác nhận", f"Xoá combo '{combo_name}'?"):
            del self.combos[combo_name]
            self.save_combos()
            self.render_combo_buttons()
            self.status_var.set(f"Đã xoá combo: {combo_name}")
    
    def edit_combo_dialog(self, combo_name):
        """Open dialog to edit an existing combo"""
        if combo_name not in self.combos:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Sửa Combo: {combo_name}")
        dialog.geometry("500x550")
        dialog.configure(bg=self.bg_color)
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        
        # Combo name
        tk.Label(dialog, text="Tên Combo:", font=("Segoe UI", 11, "bold"),
                bg=self.bg_color, fg=self.text_color).pack(pady=(15, 5))
        
        name_entry = tk.Entry(dialog, font=("Consolas", 11), bg=self.surface_color,
                             fg=self.text_color, insertbackground=self.text_color, width=30)
        name_entry.pack(pady=5)
        name_entry.insert(0, combo_name)  # Pre-fill with current name
        
        # Actions list
        tk.Label(dialog, text="Danh sách Actions (chọn từ bên trái, thêm vào bên phải):", 
                font=("Segoe UI", 10), bg=self.bg_color, fg=self.text_color).pack(pady=(15, 5))
        
        list_frame = tk.Frame(dialog, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Available actions listbox
        avail_frame = tk.Frame(list_frame, bg=self.bg_color)
        avail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(avail_frame, text="Có sẵn:", font=("Segoe UI", 9),
                bg=self.bg_color, fg=self.text_color).pack()
        
        avail_listbox = tk.Listbox(avail_frame, font=("Consolas", 10), bg=self.surface_color,
                                   fg=self.text_color, selectbackground=self.primary_color, height=12)
        avail_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        for action_name in self.available_actions.keys():
            avail_listbox.insert(tk.END, action_name)
        
        # Buttons in middle
        btn_frame = tk.Frame(list_frame, bg=self.bg_color)
        btn_frame.pack(side=tk.LEFT, padx=10)
        
        # Pre-fill with existing actions
        selected_actions = self.combos[combo_name].copy()
        
        def add_action():
            selection = avail_listbox.curselection()
            if selection:
                action = avail_listbox.get(selection[0])
                selected_actions.append(action)
                update_selected_list()
        
        def remove_action():
            selection = selected_listbox.curselection()
            if selection:
                del selected_actions[selection[0]]
                update_selected_list()
        
        def move_up():
            selection = selected_listbox.curselection()
            if selection and selection[0] > 0:
                idx = selection[0]
                selected_actions[idx], selected_actions[idx-1] = selected_actions[idx-1], selected_actions[idx]
                update_selected_list()
                selected_listbox.selection_set(idx-1)
        
        def move_down():
            selection = selected_listbox.curselection()
            if selection and selection[0] < len(selected_actions) - 1:
                idx = selection[0]
                selected_actions[idx], selected_actions[idx+1] = selected_actions[idx+1], selected_actions[idx]
                update_selected_list()
                selected_listbox.selection_set(idx+1)
        
        def update_selected_list():
            selected_listbox.delete(0, tk.END)
            for i, act in enumerate(selected_actions):
                selected_listbox.insert(tk.END, f"{i+1}. {act}")
        
        tk.Button(btn_frame, text="→", font=("Segoe UI", 12, "bold"), bg=self.green_color,
                 fg=self.bg_color, command=add_action, width=3).pack(pady=5)
        tk.Button(btn_frame, text="←", font=("Segoe UI", 12, "bold"), bg=self.accent_color,
                 fg=self.bg_color, command=remove_action, width=3).pack(pady=5)
        tk.Button(btn_frame, text="↑", font=("Segoe UI", 12, "bold"), bg=self.yellow_color,
                 fg=self.bg_color, command=move_up, width=3).pack(pady=5)
        tk.Button(btn_frame, text="↓", font=("Segoe UI", 12, "bold"), bg=self.yellow_color,
                 fg=self.bg_color, command=move_down, width=3).pack(pady=5)
        
        # Selected actions listbox
        selected_frame = tk.Frame(list_frame, bg=self.bg_color)
        selected_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(selected_frame, text="Đã chọn (theo thứ tự):", font=("Segoe UI", 9),
                bg=self.bg_color, fg=self.text_color).pack()
        
        selected_listbox = tk.Listbox(selected_frame, font=("Consolas", 10), bg=self.surface_color,
                                      fg=self.text_color, selectbackground=self.primary_color, height=12)
        selected_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Load existing actions into the list
        update_selected_list()
        
        # Save button
        def save_combo():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Lỗi", "Vui lòng nhập tên combo!")
                return
            if not selected_actions:
                messagebox.showwarning("Lỗi", "Vui lòng chọn ít nhất 1 action!")
                return
            
            # If name changed, delete old combo
            if new_name != combo_name:
                del self.combos[combo_name]
            
            self.combos[new_name] = selected_actions.copy()
            self.save_combos()
            self.render_combo_buttons()
            dialog.destroy()
            self.status_var.set(f"Đã cập nhật combo: {new_name}")
        
        tk.Button(dialog, text="💾 Lưu Combo", font=("Segoe UI", 11, "bold"),
                 bg=self.green_color, fg=self.bg_color, activebackground="#b5e8b5",
                 padx=20, pady=10, command=save_combo, borderwidth=0).pack(pady=15)
    
    # ============ NO-SWITCH ACTION HELPERS ============
    # These are called during combo execution (already switched window)
    
    def paste_user_no_switch(self):
        """Paste user without switching window"""
        user, _, _ = self.get_first_line_parts()
        if user:
            pyperclip.copy(user)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.01)
            pyautogui.hotkey('ctrl', 'v')
    
    def paste_pass_no_switch(self):
        """Paste password without switching window"""
        _, password, _ = self.get_first_line_parts()
        if password:
            pyperclip.copy(password)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.01)
            pyautogui.hotkey('ctrl', 'v')
    
    def paste_mail_no_switch(self):
        """Paste mail without switching window"""
        _, _, mail = self.get_first_line_parts()
        if mail:
            pyperclip.copy(mail)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.01)
            pyautogui.hotkey('ctrl', 'v')
    
    def paste_custom_no_switch(self):
        """Paste custom content without switching window"""
        custom_content = self.custom_content_var.get().strip()
        if custom_content and custom_content != "Nhập nội dung...":
            pyperclip.copy(custom_content)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.01)
            pyautogui.hotkey('ctrl', 'v')
    
    def tab_no_switch(self):
        """Press Tab without switching window"""
        pyautogui.press('tab')
    
    def enter_no_switch(self):
        """Press Enter without switching window"""
        pyautogui.press('enter')
    
    def fetch_code_no_switch(self):
        """Fetch code and paste without switching (for combo - synchronous)"""
        _, _, mail_user = self.get_first_line_parts()
        if not mail_user:
            return
        
        try:
            # Extract username from email
            if '@' in mail_user:
                username = mail_user.split('@')[0]
            else:
                username = mail_user
            
            attempt = 0
            while attempt < self.max_retry_attempts:
                attempt += 1
                
                api_url = f"http://localhost:3000/api/get-code?username={username.strip()}"
                response = requests.get(api_url, timeout=10)
                
                if response.status_code != 200:
                    return
                
                result = response.json()
                if not result.get('ok'):
                    return
                data = result.get('raw', [])
                code = None
                
                if isinstance(data, list) and len(data) > 0 and 'body' in data[0]:
                    body = data[0]['body']
                    
                    match = re.search(r'<b[^>]>(\d{8})</b>', body)
                    if match:
                        code = match.group(1)
                    
                    if not code:
                        match = re.search(r'\*\*(\d{8})\*\*', body)
                        if match:
                            code = match.group(1)
                    
                    if not code:
                        match = re.search(r'\b(\d{8})\b', body)
                        if match:
                            code = match.group(1)
                
                if code:
                    # Check if code is same as last fetched
                    if code == self.last_fetched_code:
                        if attempt < self.max_retry_attempts:
                            time.sleep(self.retry_delay)  # Wait and retry
                            continue
                        else:
                            return  # Give up after max retries
                    
                    # New code found!
                    self.last_fetched_code = code
                    pyperclip.copy(code)
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.02)
                    pyautogui.hotkey('ctrl', 'v')
                    return
                else:
                    return  # No code found
        except:
            pass

    def close_and_new_no_switch(self):
        """Alt+F4 -> Ctrl+Shift+N -> Go to Garena (for combo)"""
        url = "https://account.garena.com/"
        pyperclip.copy(url)
        
        pyautogui.hotkey('alt', 'F4')
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'shift', 'n')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.03)
        pyautogui.press('enter')

    def goto_url_action(self):
        """Alt+Tab -> F6 -> Paste URL -> Enter (with switch back)"""
        url = self.url_var.get().strip() if self.url_var else ""
        if not url or url == "https://":
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL!")
            return
        
        pyperclip.copy(url)
        
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.05)
        pyautogui.press('f6')
        time.sleep(0.03)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.03)
        pyautogui.press('enter')
        time.sleep(0.03)
        pyautogui.hotkey('alt', 'tab')
        self.status_var.set(f"Đã vào URL: {url[:50]}..." if len(url) > 50 else f"Đã vào URL: {url}")
    
    def goto_url_no_switch(self):
        """F6 -> Paste URL -> Enter (without switch, for combo)"""
        url = self.url_var.get().strip() if self.url_var else ""
        if not url or url == "https://":
            return
        
        pyperclip.copy(url)
        pyautogui.press('f6')
        time.sleep(0.03)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.03)
        pyautogui.press('enter')


if __name__ == "__main__":
    root = tk.Tk()
    app = AccountManager(root)
    root.mainloop()
