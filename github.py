import json

from bs4 import BeautifulSoup, Tag
import requests

ACCOUNT_FILE = 'accounts.json'

class Github:
    def __init__(self, name):
        self.name = name
        self.session = requests.Session()
        self.accounts = self.load_accounts()

    def switch_account(self, account_name):
        if account_name in self.accounts:
            self.name = account_name
            self.session.cookies.clear()
            self.session.cookies.update({
                cookie.split('=')[0].strip(): cookie.split('=')[1].strip() for cookie in self.accounts[account_name]['cookies'].split(';') if '=' in cookie
            })
        else:
            raise Exception(f"Account '{account_name}' not found.")
    
    def load_accounts(self):
        accounts = {}
        try:
            with open(ACCOUNT_FILE, "r") as f:
                accounts = json.load(f)
        except FileNotFoundError:
            pass
        return accounts

    def save_accounts(self, accounts):
        with open(ACCOUNT_FILE, "w") as f:
            json.dump(accounts, f, indent=4)
    
    def login(self):
        if len(self.accounts[self.name]['recovery_codes']) == 0:
            self.regenerate_recovery_codes()
            if len(self.accounts[self.name]['recovery_codes']) == 0:
                raise Exception("No recovery codes available. Please regenerate them manually.")
         
        page = self.session.get('https://github.com/login')
        soup = BeautifulSoup(page.content, "html.parser")
        form = soup.select_one('form[action="/session"]:not([class])')
        if isinstance(form, Tag):
            authenticity_token = form.select_one('input[name="authenticity_token"]').get("value")
            required_field_name = form.select_one('input[name*="required_field"]').get("name")
            timestamp = form.select_one('input[name="timestamp"]').get("value")
            timestamp_secret = form.select_one('input[name="timestamp_secret"]').get("value")
            
            form_data = {
                "commit": "Sign in",
                "authenticity_token": authenticity_token,
                "login": self.name,
                "password": self.accounts[self.name]['password'],
                "webauthn-conditional": "undefined",
                "javascript-support": "true",
                "webauthn-support": "supported",
                "webauthn-iuvpaa-support": "supported",
                "return_to": 'https://github.com/login',
                f"{required_field_name}": '',
                "timestamp": timestamp,
                "timestamp_secret": timestamp_secret,
            }
            response = self.session.post('https://github.com/session', data=form_data)
            
            page = self.session.get('https://github.com/sessions/two-factor/recovery')
            soup = BeautifulSoup(page.content, "html.parser")
            if soup:
                authenticity_token = soup.select_one('input[name="authenticity_token"]').get("value")
                response = self.session.post('https://github.com/sessions/two-factor/recovery', data={
                    "authenticity_token": authenticity_token,
                    "recovery_code": self.accounts[self.name]['recovery_codes'].pop(0)
                })
                if response.status_code == 200:
                    print("Login successful!")
                    cookie_str = "; ".join(f"{name}={value}" for name, value in self.session.cookies.items())
                    self.accounts[self.name]['cookies'] = cookie_str
                    self.save_accounts(self.accounts)
                    return
                self.save_accounts(self.accounts)
                    
            raise Exception(f"Failed to login: {response.status_code} - {response.text}")
  
    def regenerate_recovery_codes(self):
        url = 'https://github.com/settings/auth/recovery-codes'
        page = self.session.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        authenticity_token = soup.select_one('form[action="/settings/auth/recovery-codes"] input[name="authenticity_token"]').get("value")
        page = self.session.post(
            url,
            data={
                "authenticity_token": authenticity_token,
                "_method": "put"
            }
        )
        soup = BeautifulSoup(page.content, "html.parser")
        new_codes = [code.text.strip() for code in soup.select('ul.two-factor-recovery-codes li')]
        self.accounts[self.name]['recovery_codes'] = new_codes
        self.save_accounts(self.accounts)

    def get_usage(self):
        page = self.session.get('https://github.com/settings/copilot/features')
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, 'html.parser')
            form = soup.find('form', {'data-target': 'copilot-user-settings.form'})
            if not form or not isinstance(form, Tag):            
                raise Exception("Could not find usage data on the page.")
            items = form.select('.StackItem .Stack span:nth-child(2)')
            if len(items) < 2:
                raise Exception("Could not find usage data on the page.")
            completions_usage_str = items[0].text.strip()
            chat_usage_str = items[1].text.strip()
            
            reset_str = ''
            reset_day_span = form.select_one('.Box-footer div span')
            if reset_day_span:
                reset_day_str = reset_day_span.text.strip()
                if 'reset in' in reset_day_str:
                    reset_str = f" (resets in {reset_day_str.split('reset in')[1].strip()})"
            return completions_usage_str, chat_usage_str, reset_str
        else:
            raise Exception(f"Failed to get usage data: {page.status_code} - {page.text}")

if __name__ == "__main__":
    github = Github("greenlanddd2")
    github.get_usage()