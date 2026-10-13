# Unofficial integration disclaimer

suno-mcp is **not** affiliated with, endorsed by, or supported by Suno Inc.

## How it works

v2 uses the community **paperfoot/suno-cli** tool, which calls the same private web APIs the Suno website uses, authenticated with **your** Suno account (Clerk session / JWT).

## Your responsibilities

- You must comply with [Suno's Terms of Service](https://suno.com/terms) and acceptable use.
- Automation may trigger captchas, rate limits, or account review.
- Generated music remains subject to Suno's licensing rules for your subscription tier.

## No warranty

Maintainers do not guarantee continued operation when Suno changes auth, captcha, or API shapes. There is no SLA.

## Official Suno APIs

The only documented public Suno API today is **C2PA provenance detection** (see suno.com/suno-credentials). A curated partner generation API was announced for exploration in July 2026; it is not generally available.

## Reseller APIs

Third-party gateways (TTAPI, sunoapi.org, etc.) are separate products with separate billing and terms. suno-mcp v2 does not use them by default.
