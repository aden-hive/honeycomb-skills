---
name: honeycomb-news-sentiment
description: Search Google News RSS for AI automation related to a job ticker and return a sentiment score from -1 to +1. Use when evaluating a job position's AI automation risk or sentiment.
license: Apache-2.0
compatibility: Requires network access to Google News RSS
allowed-tools: Bash(python:*)
metadata:
  author: aden-hive
  version: "1.0"
---

# HoneyComb News Sentiment

Analyze news sentiment regarding AI automation for specific job position tickers on the HoneyComb exchange. It queries Google News RSS and calculates a sentiment score indicating whether recent news points towards automation (negative for the job) or not (positive for the job).

## How it works

1. **Input**: A job ticker like `$SWE` (or just `SWE`).
2. **Search**: Translates the ticker to a job title and queries Google News RSS for `"{job title} AI automation"`.
3. **Analyze**: Parses the news headlines and descriptions.
4. **Output**: Returns a sentiment score from -1 to +1, where -1 means highly negative regarding the job's future (high automation risk) and +1 means positive (low automation risk or AI augmenting the role positively).

## Usage

You can use the included `scripts/sentiment.py` script to run the analysis from the `honeycomb-news-sentiment` directory:

```bash
cd honeycomb-news-sentiment
python3 scripts/sentiment.py SWE
```

### Response Format

The script outputs a JSON object containing the sentiment analysis results:

```json
{
  "ticker": "SWE",
  "job_title": "Software Engineer",
  "query": "Software Engineer AI automation",
  "articles_analyzed": 10,
  "sentiment_score": -0.45,
  "article_scores": [
    {
      "title": "Example Article Title",
      "score": -0.45
    }
  ]
}
```

## Ticker Mapping

The script includes a basic mapping of tickers to job titles:
- `SWE` -> Software Engineer
- `PM` -> Product Manager
- `DATA` -> Data Scientist
- `DESIGN` -> UI/UX Designer
- `CPA` -> Accountant
- `HR` -> Human Resources
- `NURSE` -> Nurse
- `TEACHER` -> Teacher
- `TRADER` -> Financial Trader
- `LAWYER` -> Lawyer
