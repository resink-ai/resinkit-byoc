from resinkit_api.services.svc_manager import SvcManager

_service_manager: SvcManager = None


def get_service_manager():
    global _service_manager
    if not _service_manager:
        _service_manager = SvcManager()
    return _service_manager


__all__ = ["get_service_manager", "SvcManager"]
