# Copilot Instructions for This Repository

This repository is an educational Python blockchain project. When editing code here, keep changes small, local, and consistent with the surrounding style.

## General editing rules

- Preserve existing public APIs unless a change is clearly required.
- Prefer the simplest implementation that matches the current tests and code patterns.
- Keep naming, control flow, and error handling aligned with nearby code.
- Do not refactor unrelated code while filling in a placeholder.
- Use the project’s current conventions for type hints, docstrings, and exceptions.

## CHALLENGE blocks

This codebase contains `CHALLENGE` comments that intentionally mark missing logic. If asked to fill those placeholders:

- Replace the commented block with a direct implementation in the same location.
- Match the style and behavior of the nearby code rather than inventing a new abstraction.
- Keep the solution minimal and consistent with the repository’s existing tests.
- Treat the surrounding comments and tests as the source of truth for expected behavior.

## Security and validation expectations

- Prefer explicit validation before state mutation.
- Raise the existing domain-specific exceptions already used by the codebase.
- Let the existing FastAPI layer convert those exceptions into the current HTTP responses.

## If you are filling a placeholder

- Use the smallest change that makes the current tests pass.
- Preserve the current shape of the function or method.
- Do not introduce extra dependencies.
- Do not change behavior outside the challenged code path unless necessary for correctness.
