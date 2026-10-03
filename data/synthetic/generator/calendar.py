import sys
import zoneinfo
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import yaml

# Ensure backend/ is on sys.path for app.* imports
_backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.schemas.synthetic_config import CalendarConfig  # noqa: E402

DHAKA_TZ = zoneinfo.ZoneInfo("Asia/Dhaka")


class DhakaCalendar:
    """Manages Bangladesh holidays, festivals, weekends, and salary/bill cycles for 2026."""

    def __init__(self, config_path: Path | None = None) -> None:
        if config_path is None:
            config_path = Path("data/synthetic/config/calendar.yaml")
        with open(config_path, encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
        self.config = CalendarConfig.model_validate(raw_data)
        self.start_date = date.fromisoformat(self.config.start_date)
        self.end_date = date.fromisoformat(self.config.end_date)
        self.weekend_days = set(self.config.weekend_days)
        self.festivals = self.config.festivals

    def is_weekend(self, d: date) -> bool:
        """Return True if date is a Bangladeshi weekend (Friday=4, Saturday=5)."""
        return d.weekday() in self.weekend_days

    def is_ramadan(self, d: date) -> bool:
        """Check if date falls within Ramadan 2026."""
        fest = self.festivals.get("ramadan_2026")
        if not fest or not fest.start_date or not fest.end_date:
            return False
        return date.fromisoformat(fest.start_date) <= d <= date.fromisoformat(fest.end_date)

    def is_eid_ul_fitr(self, d: date) -> bool:
        """Check if date is during Eid-ul-Fitr holidays."""
        fest = self.festivals.get("eid_ul_fitr_2026")
        if not fest or not fest.festival_start or not fest.festival_end:
            return False
        return date.fromisoformat(fest.festival_start) <= d <= date.fromisoformat(fest.festival_end)

    def is_eid_ul_fitr_shopping(self, d: date) -> bool:
        """Check if date is within pre-Eid-ul-Fitr shopping rush."""
        fest = self.festivals.get("eid_ul_fitr_2026")
        if not fest or not fest.shopping_start or not fest.shopping_end:
            return False
        return date.fromisoformat(fest.shopping_start) <= d <= date.fromisoformat(fest.shopping_end)

    def is_eid_ul_adha(self, d: date) -> bool:
        """Check if date is during Eid-ul-Adha holidays."""
        fest = self.festivals.get("eid_ul_adha_2026")
        if not fest or not fest.festival_start or not fest.festival_end:
            return False
        return date.fromisoformat(fest.festival_start) <= d <= date.fromisoformat(fest.festival_end)

    def is_eid_ul_adha_qurbani(self, d: date) -> bool:
        """Check if date is in Eid-ul-Adha cattle market / qurbani preparation window."""
        fest = self.festivals.get("eid_ul_adha_2026")
        if not fest or not fest.qurbani_window_start or not fest.qurbani_window_end:
            return False
        return (
            date.fromisoformat(fest.qurbani_window_start)
            <= d
            <= date.fromisoformat(fest.qurbani_window_end)
        )

    def is_pohela_boishakh(self, d: date) -> bool:
        """Check if date is Pohela Boishakh (Bengali New Year)."""
        fest = self.festivals.get("pohela_boishakh_2026")
        if not fest or not fest.date:
            return False
        return d == date.fromisoformat(fest.date)

    def get_category_multiplier(self, category: str, d: date) -> Decimal:
        """Calculate spend volume/probability multiplier for a given category on date d."""
        mult = Decimal("1.00")

        # 1. Ramadan Effects
        if self.is_ramadan(d):
            if category in ("groceries", "bazaar"):
                mult *= Decimal("1.35")
            elif category in ("charity", "zakat", "donation"):
                mult *= Decimal("2.50")
            elif category == "dining":
                mult *= Decimal("0.80")  # Daytime dining zero, evening dining heavy

        # 2. Pre-Eid-ul-Fitr Shopping Rush
        if self.is_eid_ul_fitr_shopping(d):
            if category in ("shopping", "clothing"):
                mult *= Decimal("3.20")
            elif category in ("travel", "transport"):
                mult *= Decimal("2.20")
            elif category in ("family_support", "send_money"):
                mult *= Decimal("2.00")

        # 3. Eid-ul-Adha Qurbani window
        if self.is_eid_ul_adha_qurbani(d):
            if category in ("cash_out", "livestock_qurbani"):
                mult *= Decimal("2.80")
            elif category in ("travel", "transport"):
                mult *= Decimal("2.00")

        # 4. Pohela Boishakh
        if self.is_pohela_boishakh(d) and category in ("dining", "entertainment", "shopping"):
            mult *= Decimal("1.80")

        # 5. Weekend Leisure vs Weekday Commute
        if self.is_weekend(d):
            if category in ("dining", "entertainment"):
                mult *= Decimal("1.40")
            elif category in ("groceries", "bazaar"):
                mult *= Decimal("1.30")  # Friday morning bazaar is a national tradition
            elif category == "transport":
                mult *= Decimal("0.70")
        else:
            if category == "transport":
                mult *= Decimal("1.25")

        return mult

    def make_dhaka_datetime(self, d: date, hour: int, minute: int, second: int = 0) -> datetime:
        """Create a timezone-aware datetime in Asia/Dhaka."""
        return datetime.combine(d, time(hour, minute, second), tzinfo=DHAKA_TZ)
