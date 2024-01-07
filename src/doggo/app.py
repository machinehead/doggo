import os
from typing import TYPE_CHECKING, Any

import psutil
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

if TYPE_CHECKING:
    from datadog.dogstatsd.base import DogStatsd
else:
    from datadog.dogstatsd import DogStatsd

HOSTNAME = os.environ["DOGGO_HOSTNAME"]

dd_client = DogStatsd(
    host=os.environ["DD_HOSTNAME"], port=8125, constant_tags=[f"hostname:{HOSTNAME}"]
)

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, Any]:
    return {
        "loadavg": psutil.getloadavg(),
        "cpu_times_percent": psutil.cpu_times_percent(
            interval=None, percpu=False
        )._asdict(),
        "net_io_counters": psutil.net_io_counters(pernic=True),
    }


@app.on_event("startup")
@repeat_every(seconds=5)
def report_metrics() -> None:
    loadavg = psutil.getloadavg()
    dd_client.gauge("system.load.1", loadavg[0])
    dd_client.gauge("system.load.5", loadavg[1])
    dd_client.gauge("system.load.15", loadavg[2])
    cpu_percent = psutil.cpu_times_percent(interval=None, percpu=False)
    for key, value in cpu_percent._asdict().items():
        dd_client.gauge(f"system.cpu.{key}", value)
    memory = psutil.virtual_memory()
    # svmem(total=10367352832, available=6472179712, percent=37.6, used=8186245120, free=2181107712, active=4748992512,
    #       inactive=2758115328, buffers=790724608, cached=3500347392, shared=787554304)
    dd_client.gauge("system.mem.usable", memory.available // 1024 // 1024)
    dd_client.gauge("system.mem.total", memory.total // 1024 // 1024)
