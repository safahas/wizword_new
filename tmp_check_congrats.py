from backend.share_card import create_congrats_sei_card
import os

p = create_congrats_sei_card('testuser','animals',2.34)
print(p)
print('exists:', os.path.exists(p)) 