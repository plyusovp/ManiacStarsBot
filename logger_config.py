# logger_config.py
import logging
import sys

from pythonjsonlogger import jsonlogger

from config import settings


class SecretMasker(logging.Filter):
    """Фильтр для маскирования секретов в логах."""

    def filter(self, record):
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = record.msg.replace(settings.BOT_TOKEN, "***BOT_TOKEN***")
        # Also check args
        if record.args:
            cleaned_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    cleaned_args.append(
                        arg.replace(settings.BOT_TOKEN, "***BOT_TOKEN***")
                    )
                else:
                    cleaned_args.append(arg)
            record.args = tuple(cleaned_args)
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Кастомный форматер для добавления кастомных полей."""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record["timestamp"] = log_record.get(
            "asctime", self.formatTime(record, self.datefmt)
        )
        log_record["level"] = record.levelname
        log_record["module"] = record.name

        # Удаляем дублирующиеся или ненужные поля
        for field in [
            "asctime",
            "levelname",
            "name",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "process",
            "processName",
        ]:
            if field in log_record:
                del log_record[field]


def setup_logging():
    """Настраивает структурированное логирование в JSON."""
    log_formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(module)s %(message)s %(user_id)s %(trace_id)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_formatter)
    handler.addFilter(SecretMasker())

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True,  # Переопределяем любую существующую конфигурацию
    )
    logging.info("Logging configured successfully.")
