import os
import subprocess
import chardet

def is_utf8(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    return result['encoding'] == 'utf-8'

def remove_non_utf8(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    try:
        content.decode('utf-8')  # Check if the content is utf-8
    except UnicodeDecodeError:
        # Remove non-UTF-8 characters
        content = content.decode('utf-8', 'ignore').encode('utf-8')
    with open(file_path, 'wb') as f:
        f.write(content)

def traverse_git_tree(root):
    # Get all tracked files in the git repository
    result = subprocess.run(['git', 'ls-files'], stdout=subprocess.PIPE)
    files = result.stdout.decode('utf-8').splitlines()
    for file_path in files:
        full_path = os.path.join(root, file_path)
        if os.path.isfile(full_path):
            if not is_utf8(full_path):
                print(f'Removing non-utf-8 characters from: {full_path}')
                remove_non_utf8(full_path)

if __name__ == '__main__':
    repo_root = os.getcwd()
    traverse_git_tree(repo_root)