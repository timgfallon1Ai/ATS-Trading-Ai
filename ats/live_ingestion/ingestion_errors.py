class IngestionError(Exception):
    """Base ingestion failure."""


class StreamDisconnectError(IngestionError):
    """Stream disconnected unexpectedly."""


class StreamDataError(IngestionError):
    """Invalid or incomplete data received from streaming provider."""
