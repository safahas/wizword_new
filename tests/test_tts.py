from backend.tts import hash_key, to_ssml


def test_hash_stable():
    h1 = hash_key("hola", "es", "Lucia", 1.0)
    h2 = hash_key("hola", "es", "Lucia", 1.0)
    assert h1 == h2
    assert len(h1) == 40


def test_ssml_limits():
    s1 = to_ssml("texto", "es", 0.2)   # clamps to 0.8
    assert 'rate="80%"' in s1
    s2 = to_ssml("texto", "es", 2.0)   # clamps to 1.2
    assert 'rate="120%"' in s2


