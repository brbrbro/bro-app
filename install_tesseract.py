import paramiko
import time
import sys

hostname = '106.53.188.248'
username = 'ubuntu'
password = 'Brody20260509@'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("Connecting to server...", flush=True)
client.connect(hostname, username=username, password=password, timeout=30, banner_timeout=30)
print("Connected!\n", flush=True)

def run_command(cmd, description, timeout=120):
    print(f"=== {description} ===", flush=True)
    print(f"Command: {cmd}\n", flush=True)
    
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True, timeout=timeout)
    
    # Handle sudo password
    if 'sudo' in cmd:
        time.sleep(1)
        stdin.write(password + '\n')
        stdin.flush()
    
    # Read output
    output = ""
    error = ""
    
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(1024).decode('utf-8', errors='replace')
            output += chunk
            print(chunk, end='', flush=True)
        if stderr.channel.recv_stderr_ready():
            chunk = stderr.channel.recv_stderr(1024).decode('utf-8', errors='replace')
            error += chunk
            print(chunk, end='', flush=True, file=sys.stderr)
        time.sleep(0.1)
    
    # Get remaining output
    exit_status = stdout.channel.recv_exit_status()
    
    remaining = stdout.read().decode('utf-8', errors='replace')
    if remaining:
        output += remaining
        print(remaining, end='', flush=True)
    
    remaining_err = stderr.read().decode('utf-8', errors='replace')
    if remaining_err:
        error += remaining_err
        print(remaining_err, end='', flush=True, file=sys.stderr)
    
    print(f"\nExit status: {exit_status}\n", flush=True)
    return exit_status, output, error

# Step 1: Update apt
run_command("sudo apt-get update", "Updating package list", timeout=180)

# Step 2: Install Tesseract
run_command(
    "sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra tesseract-ocr-eng",
    "Installing Tesseract OCR and language packs",
    timeout=300
)

# Step 3: Check version
run_command("tesseract --version", "Checking Tesseract version")

# Step 4: Check languages
run_command("tesseract --list-langs", "Listing available languages")

# Step 5: Check Python pytesseract
run_command(
    "cd /var/www/bro && source venv/bin/activate && pip show pytesseract",
    "Checking Python pytesseract"
)

client.close()
print("\nAll tasks completed!", flush=True)
