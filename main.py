import json
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

ACCOUNT_FILE = 'accounts.json'

def load_accounts():
    accounts = {}
    with open(ACCOUNT_FILE, 'r') as f:
        accounts = json.load(f)
    return accounts

def save_accounts(accounts):
    with open(ACCOUNT_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)

def get_usage(cookie: str):
    headers = {
        "Cookie": f"{cookie}",
        'Referer': 'https://github.com/settings/copilot/features',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Code/1.109.2 Chrome/142.0.7444.265 Electron/39.3.0 Safari/537.36"
    }
    session = requests.Session()
    response = session.get('https://github.com/settings/copilot/features', headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # form data-target="copilot-user-settings.form"
        form = soup.find('form', {'data-target': 'copilot-user-settings.form'})
        if not form or not isinstance(form, Tag):            
            raise Exception("Could not find usage data on the page.")
        # .StackItem Stack span:nth-child(2)
        items = form.select('.StackItem .Stack span:nth-child(2)')
        if len(items) < 2:
            raise Exception("Could not find usage data on the page.")
        completions_usage_str = items[0].text.strip()
        chat_usage_str = items[1].text.strip()
        
        reset_str = ''
        reset_day_span = form.select_one('.Box-footer div span')
        if reset_day_span:
            reset_day_str = reset_day_span.text.strip()
            # Upgrade for higher limits, premium models, AI reviews. Free responses reset in 17 days.
            if 'reset in' in reset_day_str:
                reset_str = f" (resets in {reset_day_str.split('reset in')[1].strip()})"
        return completions_usage_str, chat_usage_str, reset_str
    else:
        raise Exception(f"Failed to get usage data: {response.status_code} - {response.text}")
    
def add_account(account_name, bearer_token):
    accounts = load_accounts()
    accounts[account_name] = bearer_token
    save_accounts(accounts)

def remove_account(account_name):
    accounts = load_accounts()
    if account_name in accounts:
        del accounts[account_name]
        save_accounts(accounts)
    else:
        print(f"Account '{account_name}' not found.")
    
def print_all_usage(chat=False, completions=False):
    accounts = load_accounts()
    for account_name, cookie in accounts.items():
        try:
            (completions_usage_str, chat_usage_str, reset_str) = get_usage(cookie)
            print(f"{account_name}: ", end="")
            if chat:
                print(f"  Chat: {chat_usage_str}", end="")
            if completions:
                print(f"  Completions: {completions_usage_str}", end="")
            if reset_str:
                print(f"  {reset_str}")
        except Exception as e:
            print(f"Error fetching usage for account '{account_name}': {e}")
  
if __name__ == "__main__":
    print_all_usage(completions=True, chat=False)
