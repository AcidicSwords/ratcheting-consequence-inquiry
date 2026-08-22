"""Typed failures raised by pure domain transitions."""


class DomainError(ValueError):
    """Base class for a rejected command or invalid event history."""


class InvalidCommandError(DomainError):
    """A command is incompatible with the current aggregate state."""


class InvalidTransitionError(DomainError):
    """An event cannot lawfully evolve the supplied aggregate state."""


class IdentityConflictError(DomainError):
    """An immutable identity was reused for different content."""


class EffectLifecycleError(DomainError):
    """An effect request or attempt violated its lifecycle cardinality."""
