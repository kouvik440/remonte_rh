from abc import ABC, abstractmethod


class MasseSalarialeRepositoryInterface(ABC):
    @abstractmethod
    def payroll_analytics_rows(self, start_period: str, end_period: str, department_id=None):
        raise NotImplementedError
