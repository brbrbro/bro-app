import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('106.53.188.248', username='ubuntu', password='Brody20260509@')

# Read import.py
stdin, stdout, stderr = ssh.exec_command('cat /var/www/bro/routes/import.py')
import_py = stdout.read().decode('utf-8', errors='replace')

# Read file_processor.py
stdin, stdout, stderr = ssh.exec_command('cat /var/www/bro/services/file_processor.py')
file_processor = stdout.read().decode('utf-8', errors='replace')

# Read ai_parser.py
stdin, stdout, stderr = ssh.exec_command('cat /var/www/bro/services/ai_parser.py')
ai_parser = stdout.read().decode('utf-8', errors='replace')

ssh.close()

# Save to local file
output_path = r'E:\AI code\1\import_code_check.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('=== import.py ===\n')
    f.write(import_py)
    f.write('\n\n=== file_processor.py ===\n')
    f.write(file_processor)
    f.write('\n\n=== ai_parser.py ===\n')
    f.write(ai_parser)

print(f'Files saved to {output_path}')
