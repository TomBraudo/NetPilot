def check_admin_protection():
    """
    Periodic task to verify admin device is still protected.
    """
    from services.admin_protection import ensure_admin_device_protected
    ensure_admin_device_protected()
    logger.info("Verified admin device protection") 