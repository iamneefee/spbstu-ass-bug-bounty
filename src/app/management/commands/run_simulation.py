from django.core.management import BaseCommand

from ...simulation import Simulation


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--mode', choices=['step', 'auto'], default='step')
        parser.add_argument('--lambda', type=float, default=0.6)
        parser.add_argument('--duration', type=float, default=20.0)
        parser.add_argument('--delta', type=float, default=0.5)
        parser.add_argument('--buffer-size', type=int, default=8)
        parser.add_argument('--operators', type=int, default=3)

    def handle(self, *args, **opts):
        mode = opts['mode']
        sim = Simulation(
            lambda_rate=opts['lambda'],
            duration=opts['duration'],
            delta=opts['delta'],
            buffer_size=opts['buffer_size'],
            num_devices=opts['operators'],
        )

        if mode == "step":
            self.run_step_mode(sim)
        else:
            self.run_auto_mode(sim)

    def run_step_mode(self, sim: Simulation):
        print(f"{'t':>6} | Events{' ' * 54} | Buffer{' ' * 31} | Operators{' ' * 31} | %rej")
        print("-" * 140)

        while sim.clock < sim.duration:
            events = sim.step()
            print(
                f"{sim.clock:6.2f} | "
                f"{'; '.join(events):60} | "
                f"{sim.buffer_state():37} | "
                f"{sim.devices_state():40} | "
                f"{sim.rejection_percent():5.2f}"
            )

    def run_auto_mode(self, sim: Simulation):
        while sim.clock < sim.duration:
            sim.step()

        s = sim.summary()
        print("\n---- Summary ----")
        print(f"Generated: {s['generated']}")
        print(f"Started:   {s['started']}")
        print(f"Completed: {s['completed']}")
        print(f"Rejected:  {s['rejected']}")
        print(f"Rejection %: {s['rejection_percent']:.2f}")
        print(f"Average waiting time: {sim.average_waiting_time():.2f}")
        print(f"Average service time: {sim.average_service_time():.2f}")
        print("-----------------\n")
