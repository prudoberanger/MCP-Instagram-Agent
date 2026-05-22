# tools/key_manager.py
# Redirecteur vers webhook_quota.py

from tools.webhook_quota import (
    is_quota_exceeded,
    is_service_active,
    mark_service_exhausted,
    get_services_summary,
    check_all_keys,
    SERVICE_STATUS
)
