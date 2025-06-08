import os

def check_file_for_nulls(filepath):
    """Check if a file contains null bytes and print their positions."""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
            
        null_positions = []
        for i, byte in enumerate(content):
            if byte == 0:
                null_positions.append(i)
                
        if null_positions:
            print(f"{filepath} contains {len(null_positions)} null bytes at positions: {null_positions}")
            # Print the context around the first null byte
            if null_positions:
                pos = null_positions[0]
                start = max(0, pos - 10)
                end = min(len(content), pos + 10)
                context = content[start:end]
                print(f"Context around first null byte (hex):")
                print(' '.join(f'{b:02x}' for b in context))
        else:
            print(f"{filepath} contains no null bytes")
            
    except Exception as e:
        print(f"Error checking {filepath}: {e}")

def check_directory(directory):
    """Check all Python files in directory for null bytes."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                check_file_for_nulls(filepath)

if __name__ == "__main__":
    check_directory("backend")
    print("Done checking files") 