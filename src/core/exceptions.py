class PlatformError(Exception):
    """Base error that can safely be exposed through the API."""


class InvalidDocumentError(PlatformError):
    pass


class DocumentNotFoundError(PlatformError):
    pass


class ProviderUnavailableError(PlatformError):
    pass


class ProcessingError(PlatformError):
    pass


class ConfigurationError(PlatformError):
    pass


class TemplateNotFoundError(PlatformError):
    pass
