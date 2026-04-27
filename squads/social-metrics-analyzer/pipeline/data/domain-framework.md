# Social Media Metrics Framework

## 1. Data Collection Phase
- Execute Apify actors for Instagram, Twitter, and LinkedIn.
- Extract: Follower count, Like count (comments/posts), Comment count, Share/Save count.
- Store raw JSON for processing.

## 2. Processing & Normalization Phase
- Calculate "Delta" between Current Period and Previous Period.
- Calculate Engagement Rate (Total Engagements / Reach or Followers).
- Benchmark against previous period % change.

## 3. Insight Generation Phase
- Identify top 3 performing posts per platform.
- Correlate metric spikes with specific content dates.
- Extract one "Key Driver" for growth.

## 4. Reporting Phase
- Structured summary email.
- Detailed CSV spreadsheet with time-series data.
