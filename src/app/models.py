from datetime import datetime

from django.db import models


class Source(models.Model):
    name = models.CharField(max_length=50)

    generated_count = 0
    rejected_count = 0
    completed_reports = []

    def __str__(self):
        return self.name


class Report(models.Model):
    PRIORITY_CHOICES = [(i, f"Priority {i}") for i in range(1, 6)]

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='reports')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3)
    status = models.CharField(max_length=20, default="pending")
    submitted_at = models.DateTimeField(default=datetime.now)

    submitted_time: float = None
    start_time: float = None
    end_time: float = None

    def __str__(self):
        return f"Report({self.id}, source={self.source}, p={self.priority}, {self.status})"


class Device(models.Model):
    name = models.CharField(max_length=50, default="")
    busy_until = models.FloatField(default=0.0)

    total_busy_time = 0.0
    processed_count = 0

    def is_free(self, clock: float):
        return self.busy_until <= clock

    def add_busy_time(self, time: float):
        self.total_busy_time += time
        self.processed_count += 1


class Buffer(models.Model):
    size = models.IntegerField(default=10)
    _queue = []

    @property
    def queue(self):
        return self._queue

    def is_empty(self):
        return len(self._queue) == 0

    def enqueue(self, report: Report):
        if len(self._queue) < self.size:
            self._queue.append(report)
            return True, None

        lowest = min(self._queue, key=lambda r: r.priority)
        if lowest.priority < report.priority:
            replaced = lowest
            self._queue.remove(lowest)
            lowest.status = "rejected"
            self._queue.append(report)
            return True, replaced

        report.status = "rejected"
        return False, None

    def pull_tasks(self, device, batch_by_source=True):
        if not self._queue:
            return []

        if batch_by_source:
            source_id = self._queue[0].source_id
            batch = [r for r in self._queue if r.source_id == source_id]
        else:
            batch = [self._queue.pop(0)]

        for r in batch:
            self._queue.remove(r)
            r.status = "in_progress"

        return batch
