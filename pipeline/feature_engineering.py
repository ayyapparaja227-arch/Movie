import numpy as np
import pandas as pd
import re
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class FeatureEngineer:
    """
    Industrial feature engineering pipeline with dual-model feature subset mapping,
    robust cold-start routing, and 10 advanced industrial differentiators.
    """
    def __init__(self):
        # Encoders, vocabularies, and statistics
        self.genre_map = {}
        self.language_map = {}
        self.channel_stats = {}
        
        # Unique features tracking
        self.genre_peak_months = {}
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.trending_tfidf_matrix = None
        
        # Global priors
        self.global_genre_rate = 0.0
        self.global_language_rate = 0.0
        self.global_channel_stats = {"trending_rate": 0.0, "upload_count": 0.0}
        self.global_peak_month = 10
        self.global_trending_corpus_text = []
        
        # Fit flag
        self.is_fit = False
        
        # Content-only feature columns (No creator metrics)
        self.content_feature_cols = [
            "duration_minutes",
            "hour_sin", "hour_cos",
            "dow_sin", "dow_cos",
            "month_sin", "month_cos",
            "is_weekend", "is_prime_time",
            "tag_count",
            "title_length", "title_word_count", "title_caps_ratio",
            "genre_encoded", "language_encoded",
            "clickbait_index",
            "title_tag_overlap",
            "temporal_decay",
            "trending_similarity"
        ]
        
        # Full feature columns (Includes creator metrics)
        self.full_feature_cols = self.content_feature_cols + [
            "channel_trending_rate",
            "channel_upload_count"
        ]

    def cyclical_encode(self, val, max_val):
        """Map a periodic value (hour, day, month) to 2D sine/cosine space."""
        sin_val = np.sin(2 * np.pi * val / max_val)
        cos_val = np.cos(2 * np.pi * val / max_val)
        return float(sin_val), float(cos_val)

    def extract_time_features(self, upload_time_str):
        try:
            upload_time_str = str(upload_time_str).strip()
            if upload_time_str.endswith('Z'):
                dt = datetime.strptime(upload_time_str, "%Y-%m-%dT%H:%M:%SZ")
            else:
                dt = datetime.fromisoformat(upload_time_str)
        except Exception:
            dt = datetime(2026, 1, 1, 12, 0, 0)
            
        hour = dt.hour
        dow = dt.weekday()
        month = dt.month
        
        hour_sin, hour_cos = self.cyclical_encode(hour, 24)
        dow_sin, dow_cos = self.cyclical_encode(dow, 7)
        month_sin, month_cos = self.cyclical_encode(month, 12)
        
        is_weekend = 1 if dow in [5, 6] else 0
        is_prime_time = 1 if 17 <= hour <= 22 else 0
        
        return {
            "hour_sin": hour_sin, "hour_cos": hour_cos,
            "dow_sin": dow_sin, "dow_cos": dow_cos,
            "month_sin": month_sin, "month_cos": month_cos,
            "is_weekend": is_weekend,
            "is_prime_time": is_prime_time,
            "month": month
        }

    def clean_text_and_tags(self, title, tags_input):
        if title is None or (hasattr(title, "__len__") and not isinstance(title, str)) or (not isinstance(title, str) and pd.isna(title)):
            title = ""
        else:
            title = str(title)
            
        if isinstance(tags_input, list):
            tags_str = ",".join(str(t) for t in tags_input)
            tags_list = [str(t).lower() for t in tags_input]
        elif tags_input is None or (hasattr(tags_input, "__len__") and not isinstance(tags_input, str)) or (not isinstance(tags_input, str) and pd.isna(tags_input)):
            tags_str = ""
            tags_list = []
        else:
            tags_str = str(tags_input)
            tags_list = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
            
        title_length = len(title)
        title_word_count = len(title.split())
        title_caps_ratio = sum(1 for c in title if c.isupper()) / max(title_length, 1)
        
        # Tags count
        tag_count = len(tags_list)
            
        # Feature 7: Clickbait Index (clickbait words + caps ratio)
        clickbait_words = ["shocking", "viral", "secret", "reveal", "must watch", "wait until the end", "exclusive", "insane"]
        clickbait_matches = sum(1 for w in clickbait_words if w in title.lower())
        clickbait_index = clickbait_matches * 0.2 + title_caps_ratio * 0.5
        
        # Feature 8: Title-Tag Overlap
        title_words = set(re.findall(r'\w+', title.lower()))
        tag_words = set(tags_list)
        title_tag_overlap = len(title_words.intersection(tag_words))
        
        return {
            "title_length": title_length,
            "title_word_count": title_word_count,
            "title_caps_ratio": float(title_caps_ratio),
            "tag_count": tag_count,
            "clickbait_index": float(clickbait_index),
            "title_tag_overlap": float(title_tag_overlap),
            "processed_text": f"{title} {tags_str}"
        }

    def fit(self, df):
        df = df.copy()
        
        # Ensure all columns exist defensively
        if 'genre' not in df.columns:
            df['genre'] = 'Unknown'
        if 'language' not in df.columns:
            df['language'] = 'en'
        if 'channel_title' not in df.columns:
            df['channel_title'] = 'Unknown'
        if 'is_trending' not in df.columns:
            df['is_trending'] = 0
        if 'upload_time' not in df.columns:
            df['upload_time'] = '2026-08-06T18:30:00Z'
        if 'title' not in df.columns:
            df['title'] = ''
        if 'tags' not in df.columns:
            df['tags'] = ''
            
        df['genre'] = df['genre'].fillna('Unknown').str.strip().str.title()
        df['language'] = df['language'].fillna('en').str.strip().str.lower()
        df['channel_title'] = df['channel_title'].fillna('Unknown').str.strip()
        df['is_trending'] = df['is_trending'].fillna(0).astype(int)
        
        # 1. Target encoding for genre and language with smoothing (prior=10)
        self.global_genre_rate = float(df['is_trending'].mean())
        genre_counts = df.groupby('genre')['is_trending'].count()
        genre_sums = df.groupby('genre')['is_trending'].sum()
        self.genre_map = ((genre_sums + 10 * self.global_genre_rate) / (genre_counts + 10)).to_dict()
        
        self.global_language_rate = float(df['is_trending'].mean())
        lang_counts = df.groupby('language')['is_trending'].count()
        lang_sums = df.groupby('language')['is_trending'].sum()
        self.language_map = ((lang_sums + 10 * self.global_language_rate) / (lang_counts + 10)).to_dict()
        
        # 2. Channel profiles with smoothing (prior=20)
        channel_counts = df.groupby('channel_title')['is_trending'].count()
        channel_sums = df.groupby('channel_title')['is_trending'].sum()
        channel_means = ((channel_sums + 20 * self.global_genre_rate) / (channel_counts + 20)).to_dict()
        
        self.channel_stats = {}
        for chan in channel_counts.index:
            self.channel_stats[chan] = {
                "trending_rate": float(channel_means[chan]),
                "upload_count": int(channel_counts[chan])
            }
            
        self.global_channel_stats = {
            "trending_rate": float(df['is_trending'].mean()),
            "upload_count": int(df.groupby('channel_title')['is_trending'].count().mean())
        }
        
        # 3. Peak months per genre for Temporal Decay
        parsed_dates = pd.to_datetime(df['upload_time'], errors='coerce')
        df['month'] = parsed_dates.dt.month.fillna(10).astype(int)
        
        trending_df = df[df['is_trending'] == 1]
        self.genre_peak_months = {}
        for g, sub in trending_df.groupby('genre'):
            if not sub.empty:
                self.genre_peak_months[g] = int(sub['month'].mode()[0])
        self.global_peak_month = int(trending_df['month'].mode()[0]) if not trending_df.empty else 10
        
        # 4. TF-IDF on trending titles + tags for Content Similarity
        if not trending_df.empty:
            trending_corpus = (trending_df['title'].fillna('') + " " + trending_df['tags'].fillna('')).tolist()
            try:
                valid_corpus = [doc for doc in trending_corpus if doc.strip()]
                if valid_corpus:
                    self.tfidf_vectorizer.fit(valid_corpus)
                    self.trending_tfidf_matrix = self.tfidf_vectorizer.transform(valid_corpus)
                else:
                    self.trending_tfidf_matrix = None
            except Exception:
                self.trending_tfidf_matrix = None
        
        self.is_fit = True
        return self

    def transform_row(self, row):
        if not self.is_fit:
            raise ValueError("FeatureEngineer is not fitted yet!")
            
        genre = str(row.get('genre', 'Unknown')).strip().title()
        lang = str(row.get('language', 'en')).strip().lower()
        channel = str(row.get('channel_title', '')).strip()
        
        try:
            duration = float(row.get('duration_minutes', 10.0))
            if np.isnan(duration) or duration < 1:
                duration = 10.0
        except (ValueError, TypeError):
            duration = 10.0
            
        # 1. Temporal features
        time_feats = self.extract_time_features(row.get('upload_time', ''))
        upload_month = time_feats.pop("month")
        
        # 2. Text features
        text_feats = self.clean_text_and_tags(row.get('title', ''), row.get('tags', ''))
        processed_text = text_feats.pop("processed_text")
        
        # 3. Target encodings
        genre_encoded = self.genre_map.get(genre, self.global_genre_rate)
        lang_encoded = self.language_map.get(lang, self.global_language_rate)
        
        # 4. Feature 5: Temporal Decay Factor
        peak_month = self.genre_peak_months.get(genre, self.global_peak_month)
        distance = min(abs(upload_month - peak_month), 12 - abs(upload_month - peak_month))
        temporal_decay = float(np.exp(-0.5 * distance))
        
        # 5. Feature 3: Content Similarity to trending corpus (filtering self-similarity target leak)
        trending_similarity = 0.0
        if self.trending_tfidf_matrix is not None:
            try:
                new_vec = self.tfidf_vectorizer.transform([processed_text])
                sims = cosine_similarity(new_vec, self.trending_tfidf_matrix)[0]
                if len(sims) > 1:
                    sorted_sims = np.sort(sims)
                    if sorted_sims[-1] > 0.999:
                        trending_similarity = float(sorted_sims[-2])
                    else:
                        trending_similarity = float(sorted_sims[-1])
                elif len(sims) == 1:
                    trending_similarity = float(sims[0])
            except Exception:
                trending_similarity = 0.0
        
        # 6. Cold-start detection
        cold_start = True
        channel_trending_rate = self.global_channel_stats["trending_rate"]
        channel_upload_count = self.global_channel_stats["upload_count"]
        
        if channel and channel in self.channel_stats:
            cold_start = False
            channel_trending_rate = self.channel_stats[channel]["trending_rate"]
            channel_upload_count = self.channel_stats[channel]["upload_count"]
            
        features = {
            "duration_minutes": duration,
            "genre_encoded": genre_encoded,
            "language_encoded": lang_encoded,
            "channel_trending_rate": channel_trending_rate,
            "channel_upload_count": channel_upload_count,
            "clickbait_index": text_feats.pop("clickbait_index"),
            "title_tag_overlap": text_feats.pop("title_tag_overlap"),
            "temporal_decay": temporal_decay,
            "trending_similarity": trending_similarity,
            **time_feats,
            **text_feats
        }
        
        meta = {
            "cold_start": cold_start,
            "channel_title": channel,
            "genre_is_unseen": genre not in self.genre_map,
            "language_is_unseen": lang not in self.language_map
        }
        
        return features, meta

    def transform_df(self, df):
        features_list = []
        meta_list = []
        
        for _, row in df.iterrows():
            feats, meta = self.transform_row(row.to_dict())
            features_list.append(feats)
            meta_list.append(meta)
            
        features_df = pd.DataFrame(features_list)
        meta_df = pd.DataFrame(meta_list)
        
        targets = df['is_trending'].values if 'is_trending' in df.columns else None
        return features_df, targets, meta_df
