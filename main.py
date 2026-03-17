from github import Github

def print_all_usage(github, chat=False, completions=False):
    for account_name, _ in github.accounts.items():
        try:
            github.switch_account(account_name)
            try:
                (completions_usage_str, chat_usage_str, reset_str) = github.get_usage()
            except Exception as e:
                github.login()
                (completions_usage_str, chat_usage_str, reset_str) = github.get_usage()
            print(f"{account_name}: ", end="")
            if chat:
                print(f"  Chat: {chat_usage_str}", end="")
            if completions:
                print(f"  Completions: {completions_usage_str}", end="")
            if reset_str:
                print(f"  {reset_str}")
        except Exception as e:
            print(f"Error fetching usage for account '{account_name}': {e}")
  
def main():
    github = Github("greenlanddd")
    print_all_usage(github, chat=False, completions=True)
    
if __name__ == "__main__":
    main()
