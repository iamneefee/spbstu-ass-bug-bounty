from random import uniform

from .models import Buffer, Device, Report, Source


class Simulation:
    def __init__(self, lambda_rate, duration, delta, buffer_size, num_devices, num_sources):
        self.lambda_rate = lambda_rate
        self.duration = duration
        self.delta = delta

        self.sources = [Source(name=f"S{i + 1}") for i in range(num_sources)]

        for source in self.sources:
            source.generated_count = 0
            source.rejected_count = 0
            source.completed_reports = []

        self.buffer = Buffer(size=buffer_size)
        self.devices = [Device(name=f"D{i + 1}") for i in range(num_devices)]

        for device in self.devices:
            device.total_busy_time = 0.0
            device.processed_count = 0

        self.clock = 0.0
        self.generated = 0
        self.rejected = 0
        self.completed = 0
        self.started = 0
        self.completed_reports = []
        self._report_accumulator = 0.0

    def generate_reports(self):
        events = []
        self._report_accumulator += self.lambda_rate * self.delta
        n_new = int(self._report_accumulator)
        self._report_accumulator -= n_new

        for _ in range(n_new):
            source = self.sources[int(uniform(0, len(self.sources)))]

            report = Report(
                source=source,
                priority=int(uniform(1, 5)),
            )
            report.submitted_time = self.clock

            source.generated_count += 1

            self.generated += 1
            successful, replaced = self.buffer.enqueue(report)

            if successful:
                if replaced:
                    replaced.source.rejected_count += 1
                    self.rejected += 1
                    events.append(f"replace#{self.buffer.queue.index(report)}")
                else:
                    events.append(f"gen#{self.generated - 1}")
            else:
                self.rejected += 1
                source.rejected_count += 1
                events.append(f"rej#{self.generated - 1}")

        return events

    def process_devices(self):
        events = []

        for device in self.devices:
            if device.is_free(self.clock):
                tasks = self.buffer.pull_tasks(device, batch_by_source=True)
                if tasks:
                    service_time = uniform(5, 10)
                    device.busy_until = self.clock + service_time
                    self.started += len(tasks)

                    device.add_busy_time(service_time)

                    for task in tasks:
                        task.status = "done"
                        task.start_time = self.clock
                        task.end_time = self.clock + service_time
                        self.completed += 1
                        self.completed_reports.append(task)
                        task.source.completed_reports.append(task)

                    events.append(f"start#{device.name}")

        return events

    def step(self):
        self.clock += self.delta
        events = []
        events += self.generate_reports()
        events += self.process_devices()
        return events

    def buffer_state(self):
        return f"{len(self.buffer.queue)}: {[r.priority for r in self.buffer.queue]}"

    def devices_state(self):
        return "; ".join(
            f"{d.name}:{'free' if d.is_free(self.clock) else f'busy→{d.busy_until:.1f}'}"
            for d in self.devices
        )

    def rejection_percent(self):
        return (self.rejected / self.generated * 100) if self.generated else 0

    def average_waiting_time(self):
        if not self.completed_reports:
            return 0.0
        total_wait = sum(r.start_time - r.submitted_time for r in self.completed_reports)
        return total_wait / len(self.completed_reports)

    def average_service_time(self):
        if not self.completed_reports:
            return 0.0
        total_service = sum(r.end_time - r.start_time for r in self.completed_reports)
        return total_service / len(self.completed_reports)

    def source_statistics(self):
        stats = []
        for source in self.sources:
            generated = source.generated_count
            rejected = source.rejected_count
            completed = len(source.completed_reports)
            rejection_pct = (rejected / generated * 100) if generated > 0 else 0.0

            if source.completed_reports:
                avg_wait = sum(
                    r.start_time - r.submitted_time for r in source.completed_reports
                ) / len(source.completed_reports)
            else:
                avg_wait = 0.0

            if source.completed_reports:
                avg_service = sum(
                    r.end_time - r.start_time for r in source.completed_reports
                ) / len(source.completed_reports)
            else:
                avg_service = 0.0

            stats.append({
                'source': source.name,
                'generated': generated,
                'rejected': rejected,
                'completed': completed,
                'rejection_percent': rejection_pct,
                'avg_waiting_time': avg_wait,
                'avg_service_time': avg_service,
            })
        return stats

    def device_statistics(self):
        stats = []
        for device in self.devices:
            busy_time = device.total_busy_time
            utilization = (busy_time / self.clock * 100) if self.clock > 0 else 0.0
            utilization = 100 if utilization > 100 else utilization

            stats.append({
                'device': device.name,
                'total_busy_time': busy_time,
                'processed_count': device.processed_count,
                'utilization_percent': utilization,
            })
        return stats

    def summary(self):
        return {
            "generated": self.generated,
            "started": self.started,
            "completed": self.completed,
            "rejected": self.rejected,
            "rejection_percent": self.rejection_percent(),
            "sources": self.source_statistics(),
            "devices": self.device_statistics(),
        }
