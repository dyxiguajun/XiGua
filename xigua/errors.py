"""Errors that are safe to show to the person running the CLI."""

from __future__ import annotations


class XiguaError(Exception):
    """Base class for expected, user-facing failures."""


class ConfigError(XiguaError):
    """The site configuration is missing or invalid."""


class ContentError(XiguaError):
    """A post could not be read or parsed."""


class BuildError(XiguaError):
    """The site could not be written."""
