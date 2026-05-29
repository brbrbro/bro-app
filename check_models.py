import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('106.53.188.248', username='ubuntu', password='Brody20260509@')

# Read models.py
stdin, stdout, stderr = ssh.exec_command('cat /var/www/bro/models.py')
models_py = stdout.read().decode('utf-8', errors='replace')

# Check database schema
stdin, stdout, stderr = ssh.exec_command('sqlite3 /var/www/bro/instance/bro.db ".schema import_batches"')
schema = stdout.read().decode()

# Check all tables
stdin, stdout, stderr = ssh.exec_command('sqlite3 /var/www/bro/instance/bro.db ".tables"')
tables = stdout.read().decode()

# Check uploads directory
stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/bro/uploads/')
uploads_dir = stdout.read().decode()

ssh.close()

# Save to file
output = f'''=== models.py ===
{models_py}

=== import_batches schema ===
{schema}

=== All tables ===
{tables}

=== uploads directory ===
{uploads_dir}
'''

with open('E:\\AI code\\1\\models_check.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print('Saved to E:\\AI code\\1\\models_check.txt')
