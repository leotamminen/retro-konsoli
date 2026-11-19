"""Per-game adapters. Each one drives a real game through its normal input path."""
from .kultakiri import KultakiriAdapter

ADAPTERS = {
    "kultakiri": KultakiriAdapter,
}


def get_adapter(name):
    key = name.strip().lower()
    if key not in ADAPTERS:
        known = ", ".join(sorted(ADAPTERS))
        raise SystemExit("unknown game %r (have: %s)" % (name, known))
    return ADAPTERS[key]()
