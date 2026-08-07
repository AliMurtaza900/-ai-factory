"""Diagnostics for the same configured provider chain used by the Factory."""

from .factory import configured_provider


def main() -> None:
    provider = configured_provider()
    result = provider.generate(
        "Reply with exactly: FACTORY_LLM_OK",
        system="You are a connectivity test. Do not modify files or perform actions.",
    )
    print(f"LLM provider={result.provider} model={result.model} response={result.text.strip()!r}")


if __name__ == "__main__":
    main()
