# HoneyComb Rate Limits

## Trading Limits

| Layer | Limit | Window | Scope |
|-------|-------|--------|-------|
| Global trade rate | 30 trades | 1 minute | Per user |
| Per-ticker cooldown | 1 trade | 1 second | Per user × ticker |
| HC volume | 1,000,000 HC | 1 hour | Per user |

## Price Limits

| Rule | Value | Behavior |
|------|-------|----------|
| Max price move per trade | 5% | Trade rejected if it would move price more than 5% |
| Slippage tolerance | 1% | Trade rejected if pool price drifted >1% from `expected_price` |

## Transfer Limits

| Rule | Value |
|------|-------|
| Minimum transfer | 10 HC |
| Daily transfer cap | 50,000 HC per user |
| Share threshold | Must hold 100,000+ total shares to unlock transfers |
| Transfer fee | 2% |

## Archive Upload Limits

| Rule | Value |
|------|-------|
| Max archive size | 50 MB |
| Max file in archive | 1 MB per file |

## Error Responses

When rate limited:
```
HTTP 429 Too Many Requests
{"error": "Rate limited: max 30 trades per minute"}
```

When price cap exceeded:
```
HTTP 400 Bad Request
{"error": "Price move exceeds cap"}
```

When slippage exceeded:
```
HTTP 409 Conflict
{"error": "Price changed since order was placed (expected 1.01, current 1.03)"}
```

## Recommended Agent Behavior

1. Space trades at least 1 second apart per ticker
2. Keep a running count of trades per minute — pause at 25
3. Track HC volume spent — slow down approaching 800K/hour
4. On 429: wait 5 seconds, then retry
5. On 409: re-fetch price, re-estimate, and retry immediately
6. On 400 (price cap): split into smaller orders
