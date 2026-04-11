"""
Mail.tm API Wrapper
Tạo email tạm thời và lấy mã xác thực từ mail.tm
"""

import requests
import random
import string
import re
import time

class MailTM:
    BASE_URL = "https://api.mail.tm"
    DEFAULT_PASSWORD = "Garena123!"  # Password mặc định cho tất cả mail
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        self.token = None
        self.email = None
        self.account_id = None
    
    def get_domains(self):
        """Lấy danh sách domains khả dụng"""
        try:
            resp = self.session.get(f"{self.BASE_URL}/domains")
            if resp.status_code == 200:
                data = resp.json()
                # API có thể trả về list hoặc {"hydra:member": [...]}
                if isinstance(data, list):
                    domains = data
                else:
                    domains = data.get("hydra:member", [])
                return [d["domain"] for d in domains if d.get("isActive") or d.get("domain")]
            return []
        except Exception as e:
            print(f"[MailTM] Error getting domains: {e}")
            return []
    
    def generate_username(self, length=10):
        """Tạo username ngẫu nhiên"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def create_account(self, username=None, max_retries=3):
        """
        Tạo email mới trên mail.tm
        Returns: email address hoặc None nếu lỗi
        """
        # Lấy domain khả dụng (chỉ 1 lần)
        domains = self.get_domains()
        if not domains:
            print("[MailTM] No domains available")
            return None
        
        domain = domains[0]
        
        # Tạo username nếu không có
        if not username:
            username = self.generate_username()
        
        email = f"{username}@{domain}"
        
        # Tạo account với retry
        payload = {
            "address": email,
            "password": self.DEFAULT_PASSWORD
        }
        
        for attempt in range(max_retries):
            try:
                resp = self.session.post(f"{self.BASE_URL}/accounts", json=payload)
                
                if resp.status_code == 201:
                    data = resp.json()
                    self.email = email
                    self.account_id = data.get("id")
                    print(f"[MailTM] Created: {email}")
                    return email
                elif resp.status_code == 422:
                    # Email đã tồn tại - không retry
                    print(f"[MailTM] Email exists: {email}")
                    return None
                elif resp.status_code == 429:
                    # Rate limit - retry với delay tăng dần
                    wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                    print(f"[MailTM] Rate limit, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[MailTM] Create failed: {resp.status_code} - {resp.text}")
                    return None
                    
            except Exception as e:
                print(f"[MailTM] Error creating account: {e}")
                return None
        
        print(f"[MailTM] Failed after {max_retries} retries: {email}")
        return None
    
    def login(self, email=None, password=None):
        """
        Login để lấy token
        Returns: True nếu thành công
        """
        try:
            email = email or self.email
            password = password or self.DEFAULT_PASSWORD
            
            if not email:
                print("[MailTM] No email to login")
                return False
            
            payload = {
                "address": email,
                "password": password
            }
            
            resp = self.session.post(f"{self.BASE_URL}/token", json=payload)
            
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token")
                self.email = email
                self.session.headers["Authorization"] = f"Bearer {self.token}"
                print(f"[MailTM] Logged in: {email}")
                return True
            else:
                print(f"[MailTM] Login failed: {resp.status_code}")
                return False
                
        except Exception as e:
            print(f"[MailTM] Error logging in: {e}")
            return False
    
    def get_messages(self):
        """
        Lấy danh sách messages
        Returns: list messages hoặc []
        """
        try:
            if not self.token:
                if not self.login():
                    return []
            
            resp = self.session.get(f"{self.BASE_URL}/messages")
            
            if resp.status_code == 200:
                data = resp.json()
                # API có thể trả về list hoặc {"hydra:member": [...]}
                if isinstance(data, list):
                    return data
                return data.get("hydra:member", [])
            else:
                print(f"[MailTM] Get messages failed: {resp.status_code}")
                return []
                
        except Exception as e:
            print(f"[MailTM] Error getting messages: {e}")
            return []
    
    def get_message_content(self, msg_id):
        """
        Lấy nội dung message
        Returns: dict message hoặc None
        """
        try:
            if not self.token:
                if not self.login():
                    return None
            
            resp = self.session.get(f"{self.BASE_URL}/messages/{msg_id}")
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return None
                
        except Exception as e:
            print(f"[MailTM] Error getting message: {e}")
            return None
    
    def find_verification_code(self, max_retries=10, delay=2):
        """
        Tìm mã xác thực 8 số từ mail mới nhất
        Returns: code (str) hoặc None
        """
        for attempt in range(max_retries):
            print(f"[MailTM] Finding code, attempt {attempt + 1}/{max_retries}...")
            
            messages = self.get_messages()
            
            if messages:
                # Lấy message mới nhất
                msg = messages[0]
                msg_id = msg.get("id")
                
                # Lấy nội dung đầy đủ
                content = self.get_message_content(msg_id)
                if content:
                    # Tìm trong text hoặc html
                    text = content.get("text", "") or ""
                    html = content.get("html", [""])[0] if content.get("html") else ""
                    body = text + html
                    
                    # Tìm mã 8 số
                    match = re.search(r'\b(\d{8})\b', body)
                    if match:
                        code = match.group(1)
                        print(f"[MailTM] Found code: {code}")
                        return code
            
            if attempt < max_retries - 1:
                time.sleep(delay)
        
        print("[MailTM] No code found")
        return None


# Singleton instance để giữ state giữa các lần gọi
_mail_tm_instance = None

def get_mail_tm():
    global _mail_tm_instance
    if _mail_tm_instance is None:
        _mail_tm_instance = MailTM()
    return _mail_tm_instance

def reset_mail_tm():
    global _mail_tm_instance
    _mail_tm_instance = MailTM()
    return _mail_tm_instance


# Test module
if __name__ == "__main__":
    mail = MailTM()
    
    # Test tạo email
    email = mail.create_account()
    print(f"Created: {email}")
    
    if email:
        # Test login
        if mail.login():
            print("Login OK")
            
            # Test get messages
            messages = mail.get_messages()
            print(f"Messages: {len(messages)}")
