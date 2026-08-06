import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_mock_dataset(num_rows=2000, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    
    genres = ["Thriller", "Comedy", "Drama", "Action", "Horror", "Documentary", "Sci-Fi", "Romance"]
    languages = ["en", "en", "en", "hi", "es", "ja", "ko", "fr"]
    
    # Known channels vs unknown channels
    known_channels = ["Netflix", "Warner Bros.", "MrBeast", "T-Series", "Marvel Entertainment", "A24"]
    unknown_channels = [f"Creator_{i}" for i in range(1, 100)]
    
    base_time = datetime(2026, 1, 1, 0, 0, 0)
    
    records = []
    for i in range(num_rows):
        # 1. Title and channel
        is_known_channel = random.random() < 0.35
        if is_known_channel:
            channel = random.choice(known_channels)
            title = f"{channel} Exclusive - Video #{random.randint(10, 99)}"
        else:
            channel = random.choice(unknown_channels)
            title = f"My Creative Vlog #{random.randint(1, 10)}"
            
        # 2. Genre
        genre = random.choice(genres)
        
        # 3. Duration
        if genre in ["Thriller", "Action", "Sci-Fi"]:
            duration = random.randint(45, 150)  # longer format
        elif genre == "Comedy":
            duration = random.randint(5, 30)    # short/medium format
        else:
            duration = random.randint(1, 180)
            
        # 4. Upload Time
        days_offset = random.randint(0, 180)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        upload_time = base_time + timedelta(days=days_offset, hours=hour, minutes=minute)
        upload_time_str = upload_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 5. Language
        language = random.choice(languages)
        
        # 6. Tags
        num_tags = random.randint(0, 12)
        tags_pool = ["trending", "viral", "fun", "scary", "thrill", "cinematic", "indie", "short", "vlog", "bts"]
        tags = random.sample(tags_pool, min(num_tags, len(tags_pool)))
        
        # 7. Generate a trending label based on features (with some noise)
        score = 0.0
        
        # Channel weight
        if channel in ["Netflix", "MrBeast", "Marvel Entertainment"]:
            score += 0.4
        elif channel in known_channels:
            score += 0.2
        else:
            score -= 0.1
            
        # Genre weight
        if genre in ["Thriller", "Horror"]:
            score += 0.15
        elif genre == "Romance":
            score -= 0.05
            
        # Time of day weight (prime time 17:00 to 22:00)
        if 17 <= hour <= 22:
            score += 0.15
            
        # Weekend weight (Friday afternoon to Sunday night)
        if upload_time.weekday() in [4, 5, 6]:
            score += 0.1
            
        # Duration weight (sweet spot for movies 90-120 mins, for shorts 8-15 mins)
        if 90 <= duration <= 120 or 8 <= duration <= 15:
            score += 0.1
            
        # Tag count weight
        if 4 <= num_tags <= 8:
            score += 0.08
            
        # Add random noise
        score += random.normalvariate(0, 0.15)
        
        # Threshold for trending (approx 20% trending rate)
        is_trending = 1 if score > 0.15 else 0
        
        records.append({
            "title": title,
            "channel_title": channel,
            "genre": genre,
            "duration_minutes": duration,
            "upload_time": upload_time_str,
            "language": language,
            "tags": ",".join(tags),
            "is_trending": is_trending
        })
        
    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    df = generate_mock_dataset(3000, seed=42)
    df.to_csv("data/youtube_trending.csv", index=False)
    print(f"Generated {len(df)} rows of mock data. Trending rate: {df['is_trending'].mean():.2%}")
    
    # Generate a small hostile test dataset
    df_hostile = df.head(10).copy()
    # Insert some missing/malformed rows
    df_hostile.loc[0, 'duration_minutes'] = np.nan
    df_hostile.loc[1, 'upload_time'] = "invalid_date_format"
    df_hostile.loc[2, 'genre'] = None
    df_hostile.to_csv("data/test_hostile.csv", index=False)
    print("Generated hostile test dataset.")
