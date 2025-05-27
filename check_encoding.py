import os
import chardet

def check_file_encoding(filepath):
    """Check the encoding of a file."""
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
            result = chardet.detect(raw)
            print(f"{filepath}: {result}")
            
    except Exception as e:
        print(f"Error checking {filepath}: {e}")

def check_directory(directory):
    """Check all Python files in directory for encoding."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                check_file_encoding(filepath)

if __name__ == "__main__":
    check_directory("backend")
    print("Done checking files") 