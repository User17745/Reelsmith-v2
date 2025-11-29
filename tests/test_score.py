import pytest
from app.score import compute_score
import time

def test_compute_score_basic():
    # Test with known values
    upvotes = 1000
    comments = 100
    # Age 1 hour
    created_utc = time.time() - 3600
    
    score, age = compute_score(upvotes, comments, created_utc)
    
    assert age > 0.99 and age < 1.01
    assert score > 0

def test_compute_score_zero_values():
    upvotes = 0
    comments = 0
    created_utc = time.time()
    
    score, age = compute_score(upvotes, comments, created_utc)
    
    # log1p(0) = 0
    # v = 0
    # score should be just title_boost * decay
    assert score > 0

def test_compute_score_decay():
    upvotes = 1000
    comments = 100
    
    # Fresh post
    s1, _ = compute_score(upvotes, comments, time.time())
    
    # Old post (48 hours)
    s2, _ = compute_score(upvotes, comments, time.time() - (48 * 3600))
    
    assert s1 > s2
