import pytest
from app.extract import sanitize_text

def test_sanitize_text_urls():
    text = "Check this out: https://example.com/cool-video"
    sanitized = sanitize_text(text)
    assert "[link removed]" in sanitized
    assert "https://example.com" not in sanitized

def test_sanitize_text_emails():
    text = "Contact me at user@example.com for more info."
    sanitized = sanitize_text(text)
    assert "[email removed]" in sanitized
    assert "user@example.com" not in sanitized

def test_sanitize_text_phones():
    text = "Call me at 555-123-4567."
    sanitized = sanitize_text(text)
    assert "[phone removed]" in sanitized
    assert "555-123-4567" not in sanitized

def test_sanitize_text_clean():
    text = "Just a normal reddit title with no bad stuff."
    sanitized = sanitize_text(text)
    assert sanitized == text

def test_sanitize_text_usernames():
    text = "Credit to /u/someuser for this."
    sanitized = sanitize_text(text)
    assert "/u/someuser" in sanitized
