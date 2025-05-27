import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Rename backend to backend_old and backend_clean to backend
if os.path.exists("backend_old"):
    print("Removing old backup...")
    import shutil
    shutil.rmtree("backend_old")

print("Renaming directories...")
os.rename("backend", "backend_old")
os.rename("backend_clean", "backend")

try:
    print("Importing GameLogic...")
    from backend.game_logic import GameLogic
    print("Successfully imported GameLogic")
    
    print("\nTesting GameLogic initialization...")
    game = GameLogic(word_length=5, subject="General", mode="Fun")
    print("Successfully initialized GameLogic")
    
    print("\nGame state:", game.get_game_summary())
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    
    # Restore original backend directory
    print("\nRestoring original backend directory...")
    os.rename("backend", "backend_clean")
    os.rename("backend_old", "backend") 