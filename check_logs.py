import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('106.53.188.248', username='ubuntu', password='Brody20260509@')

# Check Flask application logs
stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u bro -n 50 --no-pager')
print('Bro service logs:')
print(stdout.read().decode())

# Check nginx error logs
stdin, stdout, stderr = ssh.exec_command('sudo tail -30 /var/log/nginx/error.log')
print('\nNginx error logs:')
print(stdout.read().decode())

# Check if backend is running
stdin, stdout, stderr = ssh.exec_command('sudo systemctl status bro --no-pager')
print('\nBro service status:')
print(stdout.read().decode())

ssh.close()
