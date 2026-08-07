"""Non-destructive check that the configured model provider is reachable."""

from .openai_compatible import OpenAICompatibleProvider


def main() -> None:
    provider = OpenAICompatibleProvider()
    result = provider.generate(
        "Reply with exactly: FACTORY_LLM_OK",
        system="You are a connectivity test. Do not modify files or perform actions.",
    )
    print(f"LLM provider={result.provider} model={result.model} response={result.text.strip()!r}")


if __name__ == "__main__":
    main()
