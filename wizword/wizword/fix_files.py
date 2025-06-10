import os
import shutil

def fix_file(src_path, dst_path):
    """Fix file encoding by reading and writing with explicit UTF-8 encoding."""
    try:
        # Read the file content with UTF-8 encoding
        with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Write the content back with UTF-8 encoding
        with open(dst_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
            
        print(f"Fixed encoding for {os.path.basename(src_path)}")
    except Exception as e:
        print(f"Error fixing {os.path.basename(src_path)}: {e}")

def fix_directory(src_dir, dst_dir):
    """Fix encoding for all Python files in directory."""
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    for filename in os.listdir(src_dir):
        src_path = os.path.join(src_dir, filename)
        dst_path = os.path.join(dst_dir, filename)
        
        if os.path.isfile(src_path) and filename.endswith('.py'):
            fix_file(src_path, dst_path)
        elif os.path.isdir(src_path):
            fix_directory(src_path, os.path.join(dst_dir, filename))

if __name__ == "__main__":
    # Remove old directory if it exists
    if os.path.exists("backend_clean"):
        shutil.rmtree("backend_clean")
    
    # Create new directory and fix files
    fix_directory("backend", "backend_clean")
    print("Done fixing files") 