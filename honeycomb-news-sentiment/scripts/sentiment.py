#!/usr/bin/env python3
import sys
import urllib.parse
import urllib.request
import json
import re

try:
    from defusedxml import ElementTree as ET
except ImportError:
    print(json.dumps({"error": "defusedxml not installed. Run: pip install defusedxml"}))
    sys.exit(1)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    print(json.dumps({"error": "vaderSentiment not installed. Run: pip install vaderSentiment"}))
    sys.exit(1)

def get_job_title(ticker):
    mapping = {
        'SWE': 'Software Engineer',
        'PM': 'Product Manager',
        'DATA': 'Data Scientist',
        'DESIGN': 'UI/UX Designer',
        'CPA': 'Accountant',
        'HR': 'Human Resources',
        'NURSE': 'Nurse',
        'TEACHER': 'Teacher',
        'TRADER': 'Financial Trader',
        'LAWYER': 'Lawyer'
    }
    return mapping.get(ticker, ticker)

def analyze_article(title, description, job_title, analyzer):
    # 1. Provide VADER sentiment base (General NLP scoring, pre-instantiated analyzer passed in)
    title_vader = analyzer.polarity_scores(title)['compound']
    desc_vader = analyzer.polarity_scores(description)['compound']
    
    # TITLE gets 2x weight vs description
    vader_base = (title_vader * 2 + desc_vader) / 3
    
    text = f"{title} {title} {description}".lower()
    tokens = re.findall(r'\b\w+\b', text)
    words = set(tokens)
    
    # 2. Expanded keyword lists specifically for AI & Automation
    automation_negative = [
        'replace', 'automate', 'lost', 'obsolete', 'risk', 'threat', 'decline', 
        'layoff', 'disruption', 'eliminate', 'downsize', 'redundant', 'taking over',
        'job loss', 'unemployment', 'useless', 'displace', 'substitute', 'outsource',
        'fewer jobs', 'threaten', 'extinct', 'vulnerable', 'end of', 'replacing',
        'destroy', 'wipe out', 'job killers', 'take away'
    ]
    
    automation_positive = [
        'augment', 'help', 'assist', 'grow', 'create', 'opportunity', 'enhance', 'boost',
        'collaborate', 'empower', 'productivity', 'accelerate', 'demand', 'hiring',
        'new jobs', 'up-skill', 'upskill', 'evolution', 'valuable', 'tool', 'better',
        'improve', 'efficiency', 'partner', 'leverage', 'benefit'
    ]
    
    # 3. Job-specific context words (tuning for distinct jobs like SWE vs Nurse)
    job_context = {
        'Software Engineer': {
            'negative': ['devin', 'AI software engineer', 'auto-generate code', 'gpt-4 coding', 'no-code', 'low-code', 'replace coders'],
            'positive': ['copilot', 'pair programming', 'developer productivity', 'code review', 'faster development', 'github copilot']
        },
        'Nurse': {
            'negative': ['robot nurse', 'automated diagnosis', 'replace staff'],
            'positive': ['patient care', 'health tech', 'medical records assistance', 'triage tool', 'diagnostics support', 'reduce burnout']
        },
        'Data Scientist': {
            'negative': ['auto-ml', 'automated insights', 'replace analysts'],
            'positive': ['advanced modeling', 'data crunching', 'better predictions', 'scale analysis']
        },
        'Teacher': {
            'negative': ['ai tutor replacement', 'automated grading replacing'],
            'positive': ['personalized learning', 'classroom assistant', 'lesson planning tool', 'edtech']
        }
    }
    
    context = job_context.get(job_title, {'negative': ['completely automated', 'replaced by robot'], 'positive': ['ai tool', 'tech assistant']})
    
    custom_score = 0
    
    # We use exact phrase matching for list items that have multiple words, and token-based word matching for single words.
    for phrase in automation_negative + context['negative']:
        phrase_l = phrase.lower()
        if ' ' in phrase_l:
            if phrase_l in text:
                occurrences = text.count(phrase_l)
                custom_score -= (0.15 * occurrences)
        else:
            if phrase_l in words:
                occurrences = sum(1 for w in tokens if w == phrase_l)
                custom_score -= (0.15 * occurrences)
            
    for phrase in automation_positive + context['positive']:
        phrase_l = phrase.lower()
        if ' ' in phrase_l:
            if phrase_l in text:
                occurrences = text.count(phrase_l)
                custom_score += (0.15 * occurrences)
        else:
            if phrase_l in words:
                occurrences = sum(1 for w in tokens if w == phrase_l)
                custom_score += (0.15 * occurrences)
            
    # Combine VADER NLP scoring (0.4 weight) + Custom Automation Rules (0.6 weight)
    final_score = (vader_base * 0.4) + (custom_score * 0.6)
    
    return max(min(final_score, 1.0), -1.0)

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Please provide a ticker (e.g. $SWE)"}))
        sys.exit(1)
        
    raw_ticker = sys.argv[1]
    ticker = raw_ticker.replace('$', '').upper()
    job_title = get_job_title(ticker)
    
    query = f"{job_title} AI automation"
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    # Instantiate analyzer once to save expensive overhead
    try:
        analyzer = SentimentIntensityAnalyzer()
    except Exception as e:
        print(json.dumps({"error": f"Failed to initialize analyzer: {e}"}))
        sys.exit(1)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        articles = []
        total_score = 0
        
        channel = root.find('channel')
        if channel is not None:
            items = channel.findall('item')
            for item in items[:10]: # Analyze top 10
                title_el = item.find('title')
                desc_el = item.find('description')
                
                title = (title_el.text or "").strip() if title_el is not None else ""
                desc = (desc_el.text or "").strip() if desc_el is not None else ""
                
                score = analyze_article(title, desc, job_title, analyzer)
                total_score += score
                articles.append({
                    "title": title,
                    "score": round(score, 3)
                })
                
        avg_score = total_score / len(articles) if articles else 0
        
        result = {
            "ticker": ticker,
            "job_title": job_title,
            "query": query,
            "articles_analyzed": len(articles),
            "sentiment_score": round(max(min(avg_score, 1.0), -1.0), 3),
            "article_scores": articles
        }
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
