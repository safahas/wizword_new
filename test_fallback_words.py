import sys
try:
    from wizword.wizword.backend import fallback_words as fw
except ImportError:
    print("[ERROR] Could not import fallback_words. Check your PYTHONPATH and package structure.")
    sys.exit(1)

print("'4th_grade' in FALLBACK_WORDS:", '4th_grade' in fw.FALLBACK_WORDS)
if '4th_grade' in fw.FALLBACK_WORDS:
    print("Available word lengths in '4th_grade':", sorted(fw.FALLBACK_WORDS['4th_grade'].keys()))
    print("7-letter words in '4th_grade':", fw.FALLBACK_WORDS['4th_grade'].get(7, []))
else:
    print("'4th_grade' category not found in FALLBACK_WORDS.") 