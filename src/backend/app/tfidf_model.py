from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

class TFIDFModel:
    def __init__(self, max_features=None, ngram_range=(1, 2)):
        self.vectorizer = TfidfVectorizer(
            lowercase=True, 
            max_features=max_features, 
            ngram_range=ngram_range
        )
        self.corpus_tfidf = None
        self.corpus_texts = None
        self.df = None

    def fit_corpus(self, df, text_columns):
        """
        df: pandas DataFrame
        text_columns: list of columns to combine
        """
        self.df = df.copy()
        # Combine text columns per row
        self.corpus_texts = (
            self.df[text_columns]
            .fillna("")
            .agg(" ".join, axis=1)
            .tolist()
        )
        # Fit TF-IDF and transform corpus
        self.corpus_tfidf = self.vectorizer.fit_transform(self.corpus_texts)
        print(f"TF-IDF corpus shape: {self.corpus_tfidf.shape}")

    def compute_similarity(self, query):
        """Returns cosine similarity scores for query against corpus."""
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.corpus_tfidf).flatten()
        return scores

    def normalize_scores(self, scores):
        """Min-max normalize scores to [0, 1] range."""
        if len(scores) == 0:
            return scores
        min_val, max_val = np.min(scores), np.max(scores)
        if max_val == min_val:
            return np.ones_like(scores) if max_val > 0 else np.zeros_like(scores)
        return (scores - min_val) / (max_val - min_val)

    def rank(self, query, top_k=10, min_score=0.0):
        """
        Returns top_k rows sorted by TF-IDF similarity.
        Scores are normalized to [0, 1] range.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            min_score: Minimum normalized score threshold (0-1)
        """
        scores = self.compute_similarity(query)
        normalized_scores = self.normalize_scores(scores)
        
        print(f"Score range: min={normalized_scores.min():.4f}, max={normalized_scores.max():.4f}")
        print(f"Filtering for scores >= {min_score}")
        
        # Filter by minimum score
        valid_idx = np.where(normalized_scores >= min_score)[0]
        
        print(f"Found {len(valid_idx)} results above threshold")
        
        if len(valid_idx) == 0:
            return pd.DataFrame()
        
        # Sort by score and take top_k
        sorted_idx = valid_idx[np.argsort(-normalized_scores[valid_idx])][:top_k]
        
        top_rows = self.df.iloc[sorted_idx].copy()
        top_rows['tfidf_score'] = normalized_scores[sorted_idx]
        
        print(f"Returning {len(top_rows)} results")
        print(f"Top scores: {normalized_scores[sorted_idx[:5]]}")
        
        return top_rows.reset_index(drop=True)