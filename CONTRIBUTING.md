# Contributing

Thanks for helping improve Model Verifier.

## Development

```bash
python -m pip install -e '.[test]'
pytest -q

cd apps/web
npm install
npm run lint
npm run build
```

You can start the local API and Vite UI together from the repository root:

```bash
scripts/start.sh
```

## Pull Requests

- Keep changes focused and explain the verification you ran.
- Add or update tests for behavior changes.
- Do not commit real API keys, session cookies, private URLs, `.env` files, generated build output, or dependency directories.
- Sign commits with DCO:

```text
Signed-off-by: Your Name <you@example.com>
```

## Probe Changes

Probe prompts affect public verifier behavior. Prefer small, reviewable updates and include why the probe improves signal quality without overfitting to one provider.
