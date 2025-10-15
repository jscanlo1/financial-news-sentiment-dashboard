from transformers import BertForSequenceClassification, BertTokenizer, pipeline

from data_models import Headline

finbert = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-tone',num_labels=3)
tokenizer = BertTokenizer.from_pretrained('yiyanghkust/finbert-tone') # type: ignore

classifier = pipeline("sentiment-analysis", model=finbert, tokenizer=tokenizer) # type: ignore


def analyze_headlines(headlines: list[Headline]) -> list[Headline]:
    """
    Takes a list of Headline objects and adds sentiment analysis.

    Args:
        headlines (list[Headline])

    Returns:
        list[Headline]: same headlines with sentiment_score and sentiment_label filled
    """
    texts = [h.headline for h in headlines]
    results = classifier(texts)

    for h, r in zip(headlines, results):
        # FinBERT returns label and score
        h.sentiment_label = r["label"]
        h.sentiment_score = r["score"]

    return headlines
