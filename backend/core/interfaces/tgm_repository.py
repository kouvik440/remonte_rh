from abc import ABC, abstractmethod


class TgmRepositoryInterface(ABC):
    @abstractmethod
    def finalized_payroll_rows(self, start_period: str, end_period: str) -> list:
        raise NotImplementedError

    @abstractmethod
    def contracts_for_employees(self, employee_ids: list, start_date, end_date) -> list:
        raise NotImplementedError
