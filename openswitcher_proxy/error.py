class RecoverableError(Exception):
    pass


class ConfigurationError(RecoverableError):
    pass


class DependencyError(RecoverableError):
    pass
