import calendar
from datetime import date
import re

from rest_framework.exceptions import ValidationError


def payroll_period_bounds(period: str) -> tuple[date, date]:
    try:
        if not isinstance(period, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period):
            raise ValueError
        year, month = map(int, period.split("-"))
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, TypeError) as error:
        raise ValidationError({"periode": "La période doit être au format AAAA-MM avec une année valide."}) from error
