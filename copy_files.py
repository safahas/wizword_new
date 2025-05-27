import os
import shutil

def copy_with_encoding(src_dir, dst_dir):
    """Copy files from src_dir to dst_dir with proper encoding."""
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    for filename in os.listdir(src_dir):
        src_path = os.path.join(src_dir, filename)
        dst_path = os.path.join(dst_dir, filename)
        
        if os.path.isfile(src_path):
            try:
                # Read the file content and write it with UTF-8 encoding
                with open(src_path, 'r', encoding='utf-8', errors='ignore') as src:
                    content = src.read()
                with open(dst_path, 'w', encoding='utf-8', newline='\n') as dst:
                    dst.write(content)
                print(f"Copied {filename} with UTF-8 encoding")
            except Exception as e:
                print(f"Error copying {filename}: {e}")
        elif os.path.isdir(src_path):
            # Recursively copy subdirectories
            copy_with_encoding(src_path, dst_path)

if __name__ == "__main__":
    src_dir = "backend"
    dst_dir = "backend_new"
    copy_with_encoding(src_dir, dst_dir)
    print("Done copying files") 