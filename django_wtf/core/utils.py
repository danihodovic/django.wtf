import logging


def log_action(entity, created):
    action = "Created" if created else "Updated"
    logging.info(f"{action} {entity}")
