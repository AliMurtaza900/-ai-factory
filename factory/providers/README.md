# Model providers

The Factory's revision backend can use an OpenAI-compatible model provider without storing secrets in Git.

Configure the runtime environment:

- `AI_FACTORY_API_KEY` — API credential
- `AI_FACTORY_MODEL` — model identifier
- `AI_FACTORY_BASE_URL` — optional OpenAI-compatible `/v1` endpoint
- `AI_FACTORY_PROVIDER` — currently `openai-compatible`

The provider is intentionally not called by CI unless these environment variables are configured. This keeps ordinary tests free and prevents accidental API spending.
