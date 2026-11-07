import asyncio
from hitman_monitor import HitmanMonitor


async def main():
    monitor = HitmanMonitor()
    try:
        print(await monitor.check_for_change())
    finally:
        await asyncio.sleep(0.25)


asyncio.run(main())
