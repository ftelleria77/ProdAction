"""Module entrypoint for `python -m iso_state_synthesis`."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
