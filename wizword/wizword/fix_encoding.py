import os

def fix_file_encoding(filepath):
    """Fix file encoding and remove null bytes."""
    try:
        # Read the file in binary mode
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Remove null bytes
        content = content.replace(b'\x00', b'')
        
        # Write back with UTF-8 encoding
        with open(filepath, 'wb') as f:
            f.write(content)
            
        print(f"Fixed encoding for {filepath}")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")

def fix_directory(directory):
    """Fix encoding for all Python files in directory."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                fix_file_encoding(filepath)

if __name__ == "__main__":
    fix_directory("backend")
    print("Done fixing files") 