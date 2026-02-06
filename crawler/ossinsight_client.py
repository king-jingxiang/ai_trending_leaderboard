import requests
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class OSSInsightClient:
    def __init__(self):
        self.base_url = "https://api.ossinsight.io/v1/repos"

    def fetch_star_history(self, owner, repo, granularity="day", from_date=None, to_date=None, timeout=20, max_retries=3):
        url = f"{self.base_url}/{owner}/{repo}/stargazers/history/"
        params = {"per": granularity}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=timeout)
                response.raise_for_status()
                payload = response.json()
                rows = self._extract_rows(payload)
                history = self._to_history(rows)
                time.sleep(0.2)  # Rate limiting courtesy
                return self._normalize_history(history)
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt + 1} failed for {owner}/{repo}: {exc}")
                sleep_for = min(2 ** attempt, 8)
                time.sleep(sleep_for)
        
        logger.error(f"Failed to fetch star history for {owner}/{repo}: {last_error}")
        return None

    def _extract_rows(self, payload):
        if payload is None:
            return []
        data = payload.get("data") if isinstance(payload, dict) else payload
        if isinstance(data, dict):
            if isinstance(data.get("rows"), list):
                return data["rows"]
            if isinstance(data.get("data"), list):
                return data["data"]
            if isinstance(data.get("items"), list):
                return data["items"]
            return []
        if isinstance(data, list):
            return data
        return []

    def _to_history(self, rows):
        history = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            date_value = row.get("date") or row.get("week") or row.get("month")
            count_value = row.get("count")
            if count_value is None:
                count_value = row.get("stars")
            if count_value is None:
                count_value = row.get("stargazers")
            if count_value is None:
                count_value = row.get("total")
            if date_value is None or count_value is None:
                continue
            history.append({"date": str(date_value), "count": int(count_value)})
        return history

    def _normalize_history(self, history):
        buckets = {}
        for item in history or []:
            date_str = item.get("date")
            count = item.get("count", 0)
            d = self._parse_date(date_str)
            if not d:
                continue
            if d not in buckets or count > buckets[d]:
                buckets[d] = count
        return [{"date": d.strftime("%Y-%m-%d"), "count": buckets[d]} for d in sorted(buckets.keys())]

    def _parse_date(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        if hasattr(value, "date"):
            try:
                return value.date()
            except Exception:
                pass
        if isinstance(value, str):
            raw = value.strip()
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            except ValueError:
                pass
            if len(raw) >= 10:
                try:
                    return datetime.strptime(raw[:10], "%Y-%m-%d").date()
                except ValueError:
                    return None
        return None
