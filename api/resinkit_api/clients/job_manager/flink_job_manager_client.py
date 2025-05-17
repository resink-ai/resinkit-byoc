from flink_job_manager_api import Client
from flink_job_manager_api.api.default import get_dashboard_configuration
from flink_job_manager_api.models import DashboardConfiguration
from resinkit_api.core.config import settings


class FlinkJobManager:
    def __init__(self):
        self.client = Client(base_url=settings.FLINK_JOB_MANAGER_URL)

    def get_config(self) -> "DashboardConfiguration":
        res: DashboardConfiguration = get_dashboard_configuration.sync(client=self.client)
        return res
