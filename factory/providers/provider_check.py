"""Diagnostics for the same configured provider chain used by the Factory."""

from .factory import configured_provider


def main() -> None:
    try:
        provider = configured_provider()
        result = provider.generate(
            "Reply with exactly: FACTORY_LLM_OK",
            system="You are a connectivity test. Do not modify files or perform actions.",
        )
        print(f"LLM provider={result.provider} model={result.model} response={result.text.strip()!r}")
    except Exception as exc:
        # Provider availability is an operational condition, not a code-test failure.
        # The fallback has already attempted every configured provider and included
        # each failure in this exception message.
        print(f"Provider diagnostics: no configured provider is currently available: {exc}")


if __name__ == "__main__":
    main()
