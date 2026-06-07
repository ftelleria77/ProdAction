"""Shared exceptions for ISO state synthesis."""


class IsoCandidateEmissionError(RuntimeError):
    """Raised when the explanatory candidate emitter cannot handle a plan."""
