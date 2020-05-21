
try:
    IMPORT_ERRORS = (ModuleNotFoundError, ImportError)
except NameError:
    IMPORT_ERRORS = (ImportError, )

try:
    from time import monotonic
except IMPORT_ERRORS:
    from monotonic import monotonic

try:
    from prctl import set_name as prctl_set_name
except IMPORT_ERRORS:
    def prctl_set_name(name):
        pass


__all__ = ['monotonic', 'prctl_set_name']
