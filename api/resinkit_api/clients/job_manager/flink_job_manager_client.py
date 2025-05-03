from flink_job_manager_api import Client
from flink_job_manager_api.api.default import get_dashboard_configuration
from flink_job_manager_api.models import DashboardConfiguration
class FlinkJobManager:
    def __init__(self, host: str = "127.0.0.1", port: int = 8081):
        self.host = host
        self.port = port
        self.client = Client(host=host, port=port)

    
    def _get_dashboard_configuration(self) -> 'DashboardConfiguration':
        res: DashboardConfiguration = get_dashboard_configuration.sync(client=self.client)
        return res
        
    

job_manager = FlinkJobManager()