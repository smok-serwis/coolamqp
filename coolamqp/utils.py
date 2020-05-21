try:
    from time import monotonic
except ImportError:
    from monotonic import monotonic


__all__ = ['monotonic']