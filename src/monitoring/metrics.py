import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RequestMetrics:
    question: str
    intent: str
    total_time: float
    planner_time: float
    orchestration_time: float
    success: bool
    cache_hit: bool = False
    retry_count: int = 0
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class MetricsCollector:

    def __init__(self):
        self.records = []

    def record(
        self,
        question: str,
        intent: str,
        total_time: float,
        planner_time: float,
        orchestration_time: float,
        success: bool,
        cache_hit: bool = False,
        retry_count: int = 0,
        error: Optional[str] = None,
    ):
        metric = RequestMetrics(
            question=question,
            intent=intent,
            total_time=round(total_time, 4),
            planner_time=round(planner_time, 4),
            orchestration_time=round(
                orchestration_time,
                4,
            ),
            success=success,
            cache_hit=cache_hit,
            retry_count=retry_count,
            error=error,
        )

        self.records.append(metric)

        return metric

    def summary(self):

        if not self.records:
            return {
                "requests": 0,
                "success_rate": 0,
                "avg_latency": 0,
            }

        total = len(self.records)

        successful = sum(
            1
            for record in self.records
            if record.success
        )

        avg_latency = (
            sum(
                record.total_time
                for record in self.records
            )
            / total
        )

        return {
            "requests": total,
            "success_rate": round(
                successful / total * 100,
                2,
            ),
            "avg_latency": round(
                avg_latency,
                4,
            ),
        }

    def export(self):
        return [
            record.to_dict()
            for record in self.records
        ]