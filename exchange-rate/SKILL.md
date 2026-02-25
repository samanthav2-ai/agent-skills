---
name: exchange-rate
description: Real-time forex and cryptocurrency exchange rate lookup and amount conversion powered by QVeris. Supports multiple providers with fallback for reliability.
env:
  - QVERIS_API_KEY
credentials:
  required:
    - QVERIS_API_KEY
  primary_env: QVERIS_API_KEY
  scope: read-only
  endpoint: https://qveris.ai/api/v1
network:
  outbound_hosts:
    - qveris.ai
auto_invoke: true
source: https://qveris.ai
examples:
  - "What is the USD to EUR exchange rate?"
  - "Convert 1000 USD to JPY"
  - "CNY to USD rate"
  - "100 EUR to GBP"
---

# Exchange Rate

Real-time currency exchange rate and conversion using QVeris tools.

## What This Skill Does

1. **Rate lookup** -- Current exchange rate between two currencies
2. **Amount conversion** -- Convert an amount at current rates

## Core Workflow

1. Parse user intent: **rate** or **convert**
2. Search QVeris for tools
3. Rank by success_rate, latency, and parameter fit
4. Execute with fallback across providers
5. Return formatted result

## Command Surface

- Get rate: `node scripts/exchange_rate.mjs rate --from USD --to EUR`
- Convert: `node scripts/exchange_rate.mjs convert --from USD --to JPY --amount 1000`
- Historical: add `--date YYYY-MM-DD`
- Machine-readable: add `--format json`

## Setup

Set the QVeris API key:
```bash
export QVERIS_API_KEY="your-key-here"
```

## Safety

- Uses only `QVERIS_API_KEY`; no other secrets
- Calls only QVeris over HTTPS
- Output is for reference only; not financial advice
