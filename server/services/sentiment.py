# server/services/sentiment.py
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

def classify_sentiment(text: str) -> tuple[str, float]:
    """
    Returns (label, confidence). Labels: 'positive' | 'neutral' | 'negative'
    """
    if not text or not text.strip():
        return "neutral", 0.0
    scores = _analyzer.polarity_scores(text)
    comp = scores["compound"]
    if comp >= 0.2:
        return "positive", comp
    if comp <= -0.2:
        return "negative", -comp
    return "neutral", 1.0 - abs(comp)

def sentiment_emoji(label: str) -> str:
    return {"positive": "😊", "neutral": "🙂", "negative": "😕"}.get(label, "🙂")
