import paramiko
import time

hostname = '106.53.188.248'
username = 'ubuntu'
password = 'Brody20260509@'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("Connecting...")
client.connect(hostname, username=username, password=password, timeout=30, banner_timeout=30)
print("Connected!\n")

def run_command(cmd, timeout=180):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True, timeout=timeout)
    
    if 'sudo' in cmd:
        time.sleep(1)
        stdin.write(password + '\n')
        stdin.flush()
    
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')
    
    print(f"Exit: {exit_status}")
    if output:
        print(f"Output:\n{output[:2000]}")
    if error and error.strip():
        print(f"Error:\n{error[:1000]}")
    print("-" * 50)
    return exit_status, output, error

# Check if tesseract is already installed
run_command("which tesseract")
run_command("tesseract --version")

# Try installing again with just tesseract-ocr first
run_command("sudo apt-get install -y tesseract-ocr", timeout=300)

# Then install language packs
run_command("sudo apt-get install -y tesseract-ocr-chi-sim tesseract-ocr-chi-tra tesseract-ocr-eng", timeout=300)

# Verify
run_command("tesseract --version")
run_command("tesseract --list-langs")

# Check Python environment
run_command("cd /var/www/bro && source venv/bin/activate && pip show pytesseract")

client.close()
print("Done!")
