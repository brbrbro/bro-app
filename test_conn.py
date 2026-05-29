import paramiko
import sys

hostname = '106.53.188.248'
username = 'ubuntu'
password = 'Brody20260509@'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("Connecting...", flush=True)
try:
    client.connect(hostname, username=username, password=password, timeout=30, banner_timeout=30)
    print("Connected!", flush=True)
    
    stdin, stdout, stderr = client.exec_command("echo 'Hello from server'")
    output = stdout.read().decode()
    print(f"Output: {output}", flush=True)
    
    client.close()
    print("Done", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
    sys.exit(1)
