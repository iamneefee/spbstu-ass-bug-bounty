import pandas as pd
from django.core.management import BaseCommand

from ...simulation import Simulation


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--mode', choices=['step', 'auto'], default='step')
        parser.add_argument('--sources', type=int, default=1)
        parser.add_argument('--lambda', type=float, default=1)
        parser.add_argument('--duration', type=float, default=30.0)
        parser.add_argument('--delta', type=float, default=0.5)
        parser.add_argument('--buffer-size', type=int, default=3)
        parser.add_argument('--operators', type=int, default=2)

    def handle(self, *args, **opts):
        mode = opts['mode']
        sim = Simulation(
            num_sources=opts['sources'],
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
        step_data = []

        while sim.clock < sim.duration:
            events = sim.step()
            step_data.append({
                'time': sim.clock,
                'buffer_count': len(sim.buffer.queue),
                'busy_devices': sum(1 for d in sim.devices if not d.is_free(sim.clock)),
                'events_count': len(events),
                'rejection_percent': sim.rejection_percent()
            })

        s = sim.summary()

        summary_data = {
            'Показатель': [
                'Общее время',
                'Сгенерировано',
                'Завершено',
                'Отклонено',
                'Процент отказа в системе',
                'Среднее время ожидания',
                'Среднее время обслуживания',
                'Среднее время в системе'
            ],
            'Значение': [
                f"{sim.duration:.2f}",
                f"{s['generated']}",
                f"{s['completed']}",
                f"{s['rejected']}",
                f"{s['rejection_percent']:.2f}",
                f"{sim.average_waiting_time():.2f}",
                f"{sim.average_service_time():.2f}",
                f"{sim.average_service_time() + sim.average_waiting_time():.2f}"
            ]
        }

        summary_df = pd.DataFrame(summary_data)

        sources_data = []
        for source_stat in s['sources']:
            sources_data.append({
                'Источник |': f"{source_stat['source']} |",
                'Сгенерировано |': f"{source_stat['generated']} |",
                'Отклонено |': f"{source_stat['rejected']} |",
                'P отказа |': f"{source_stat['rejection_percent']:.2f} |",
                'T ожидания |': f"{source_stat['avg_waiting_time']:.2f} |",
                'T обслуживания |': f"{source_stat['avg_service_time']:.2f} |",
                'T в системе |': f"{source_stat['avg_service_time'] + source_stat['avg_waiting_time']:.2f} |"
            })

        sources_df = pd.DataFrame(sources_data)

        devices_data = []
        for device_stat in s['devices']:
            devices_data.append({
                'Прибор |': f"{device_stat['device']} |",
                'Время работы |': f"{device_stat['total_busy_time']:.2f} |",
                'Обработано |': f"{device_stat['processed_count']} |",
                'P загруженности |': f"{device_stat['utilization_percent']:.2f} |"
            })

        devices_df = pd.DataFrame(devices_data)

        print("Итоги симуляции:")
        print(summary_df.to_string(index=False))

        print("\n\nСтатистика по источникам:")
        print(sources_df.to_string(index=False))

        print("\n\nСтатистика по приборам:")
        print(devices_df.to_string(index=False))
