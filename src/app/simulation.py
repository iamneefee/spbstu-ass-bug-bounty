from random import uniform

from .models import Buffer, Device, Report


class Simulation:
    def __init__(self, lambda_rate, duration, delta, buffer_size, num_devices):
        self.lambda_rate = lambda_rate
        self.duration = duration
        self.delta = delta

        self.buffer = Buffer(size=buffer_size)
        self.devices = [Device(name=f"O{i + 1}") for i in range(num_devices)]

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
            report = Report(
                researcher_name=f"S{int(uniform(1, 5))}",
                priority=int(uniform(1, 5)),
            )
            report.submitted_time = self.clock

            self.generated += 1
            successful, replaced = self.buffer.enqueue(report)

            if successful:
                if replaced:
                    events.append(f"replace#{self.buffer.queue.index(report)}")
                else:
                    events.append(f"gen#{self.generated - 1}")
            else:
                self.rejected += 1
                events.append(f"rej#{self.generated - 1}")

        return events

    def process_devices(self):
        events = []

        for device in self.devices:
            if device.is_free(self.clock):
                tasks = self.buffer.pull_tasks(device)
                if tasks:
                    service_time = uniform(1, 5)
                    device.busy_until = self.clock + service_time
                    self.started += len(tasks)

                    for t in tasks:
                        t.status = "done"
                        t.start_time = self.clock
                        t.end_time = self.clock + service_time
                        self.completed += 1
                        self.completed_reports.append(t)

                    events.append(f"start@{device.name}")

        return events

    def step(self):
        self.clock += self.delta
        events = []
        events += self.generate_reports()
        events += self.process_devices()
        return events

    def buffer_state(self):
        return f"{len(self.buffer.queue)} -> {[r.priority for r in self.buffer.queue]}"

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

    def summary(self):
        return {
            "generated": self.generated,
            "started": self.started,
            "completed": self.completed,
            "rejected": self.rejected,
            "rejection_percent": self.rejection_percent(),
        }
