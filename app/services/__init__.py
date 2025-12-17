"""Service package helpers.

This module exposes a couple of tiny lambda-based helpers that other services
can use to demonstrate lambda usage across the codebase. Keep helpers minimal
and side-effect free.
"""

# filter_rows: (iterable, predicate) -> list
# Example: filter_rows(rows, lambda r: r.get('Status') == 'Approved')
filter_rows = lambda rows, pred: list(filter(pred, rows))

# map_rows: (iterable, func) -> list
# Example: map_rows(rows, lambda r: r.get('UserID'))
map_rows = lambda rows, fn: list(map(fn, rows))

__all__ = ['filter_rows', 'map_rows']
