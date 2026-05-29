import paramiko

hostname = '106.53.188.248'
username = 'ubuntu'
password = 'Brody20260509@'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("Connecting...")
client.connect(hostname, username=username, password=password, timeout=30, banner_timeout=30)
print("Connected!\n")

def run_command(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')
    
    print(f"Exit: {exit_status}")
    if output:
        print(f"Output:\n{output}")
    if error and error.strip():
        print(f"Error:\n{error}")
    print("-" * 50)
    return exit_status, output, error

# Check tesseract version
run_command("tesseract --version")

# Check installed languages
run_command("tesseract --list-langs")

# Check which language packs are installed
run_command("dpkg -l | grep tesseract-ocr")

# Check Python pytesseract
run_command("cd /var/www/bro && source venv/bin/activate && pip show pytesseract")

# Check if pytesseract is importable
run_command("cd /var/www/bro && source venv/bin/activate && python -c 'import pytesseract; print(pytesseract.get_tesseract_version())'")

client.close()
print("\nDone!")
