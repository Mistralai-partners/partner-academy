from app.retry import backoff_delays
def test_exponential_backoff():
    assert backoff_delays(3, base=0.5) == [0.5, 1.0, 2.0]
