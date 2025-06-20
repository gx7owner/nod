import subprocess
import time

TOKEN_1 = "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"


# Replace with your actual codespace names
codespaces_by_token = {
    TOKEN_1: [
        "jubilant-spork-g46v6w75794j2wrqr",
        "crispy-system-jj9g7pxrv97xfj7g6",
    ]
}

# Check Codespace by trying to SSH in
def keep_alive(codespace_name):
    ssh_command = f"gh codespace ssh -c {codespace_name} -- true"
    try:
        subprocess.run(ssh_command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True 
    except subprocess.CalledProcessError:
        return False  

# Reconnect to Codespace
def reconnect(codespace_name):
    print(f"[!] Reconnecting to {codespace_name}...")
    try:
        subprocess.run(f"gh codespace ssh -c {codespace_name}", shell=True, check=True)
        print(f"[+] Reconnected to {codespace_name}")
    except subprocess.CalledProcessError as e:
        print(f"[X] Failed to reconnect to {codespace_name}: {e}")

def authenticate_with_token(token):
    print(f"Authenticating with GitHub token...")
    subprocess.run(f'echo {token} | gh auth login --with-token', shell=True, check=True)
    print("Authenticated.")

def monitor_codespaces():
    while True:
        for token, codespaces in codespaces_by_token.items():
            try:
                authenticate_with_token(token)
                for cs in codespaces:
                    if not keep_alive(cs):
                        print(f"[!] {cs} appears to be down.")
                        reconnect(cs)
                    else:
                        print(f"[✓] {cs} is up.")
            except Exception as e:
                print(f"Error checking Codespaces for a token: {e}")
        print("Waiting 60 seconds before next check...\n")
        time.sleep(60)

if __name__ == "__main__":
    monitor_codespaces()
    
    
    
