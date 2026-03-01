from django_o11y.logging.utils import get_logger

logger = get_logger()


def log_action(entity, created):
    action = "Created" if created else "Updated"
    logger.info("entity_saved", action=action, entity=str(entity))
