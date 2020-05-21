try:
    from time import monotonic
except ImportError:
    from monotonic import monotonic

try:
    from prctl import set_name as prctl_set_name
except ImportError:
    def prctl_set_name(name):
        pass


__all__ = ['monotonic', 'prctl_set_name']
