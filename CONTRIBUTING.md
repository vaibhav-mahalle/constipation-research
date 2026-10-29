# Working rules

## Setup (once per clone)
- Run `git config core.hooksPath .githooks`. The pre-commit hook then refuses a staged `data/` file, a failing unit test, and a gitleaks finding. It needs `gitleaks` (`brew install gitleaks`).
- CI (`.github/workflows/tests.yml`) runs the same tests and a gitleaks scan of the history on each push and pull request.
- Agents: read `AGENTS.md` first. It holds facts that no other file shows.

## Commits
- One commit for one step or one decision. Keep it small.
- Subject line: what changed (50 characters or fewer).
- Body: why, and which options were rejected.
- Never commit raw data, secrets, or personal data. Run `gitleaks detect` before each push.

## Decisions
- Copy `docs/decisions/0000-template.md` to the next number. Write it before or with the change.

## Problems
- Add an entry to `docs/problems.md` when a problem took real effort to solve.

## Causal ideas
- Write the idea in `docs/decisions/` with its date before the test.
- Test it on data that the exploration did not use.
