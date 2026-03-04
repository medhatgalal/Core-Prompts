from intent_pipeline.sanitization.pass1 import sanitize_pass1


def test_san_01_pass1_normalizes_structure_deterministically() -> None:
    raw = " \ufeffHello\r\n\r\n\tWorld\x00\x1f\rTrailing   spaces   \n\n\nEnd  "
    expected = "Hello\n\nWorld\nTrailing spaces\n\nEnd"

    once = sanitize_pass1(raw)
    twice = sanitize_pass1(raw)

    assert once == expected
    assert twice == expected
