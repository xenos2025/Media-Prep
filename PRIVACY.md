# Privacy

This package runs **locally**. The CLI does not phone home.

## Data the tool may touch

- Paths and bytes of image/video files you pass via `--src` / `--input`
- Optional CSV name maps and focus maps you supply
- Generated contact sheets, CSV/JSON maps, and processed media under `--out`

## What not to put in this repo

- API tokens, `.env` files, Shopify/Admin credentials
- Customer PII, inquiry exports, or factory order sheets
- Real client media batches or filled naming maps from engagements

## Agent skill context

When an agent loads `SKILL.md`, chat may include folder paths you share.
Keep private store data in a private workspace outside the public tree.
