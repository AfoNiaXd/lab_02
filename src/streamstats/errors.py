"""Иерархия исключений пакета streamstats."""


class StreamStatsError(Exception):
    """Базовая ошибка пакета streamstats."""


class CliConfigError(StreamStatsError):
    """Неверная конфигурация CLI (неизвестная команда, конфликт флагов)."""


class UnsupportedFormatError(StreamStatsError):
    """Формат входного файла не поддерживается (не csv/jsonl) или файл пуст/без заголовка."""


class MissingColumnsError(UnsupportedFormatError):
    """В CSV-заголовке отсутствуют обязательные столбцы события."""


class InvalidEventError(StreamStatsError):
    """Событие не прошло валидацию обязательных полей."""


class InvalidTimestampError(InvalidEventError):
    """Поле timestamp не парсится как ISO 8601."""


class InvalidLevelError(InvalidEventError):
    """Значение level не входит в DEBUG/INFO/WARNING/ERROR/CRITICAL."""


class EmptySourceError(InvalidEventError):
    """Поле source пустое или состоит только из пробелов."""
