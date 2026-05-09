"""CLI entry point. Real commands land in Phase 3."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "cowork-render CLI — Phase 1 scaffolding only. "
        "Real commands land in Phase 3."
    )
    print(
        "See cowork/claude-environment/cowork-render/plan.md "
        "for the design and roadmap."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
