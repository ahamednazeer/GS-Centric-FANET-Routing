from __future__ import annotations

import argparse
import random
import time

from app.api.router import seed_simulation, emit_flood, send_data, tick
from app.db import init_db, get_session
from app.models import PriorityLevel
from app.models.schemas import SimSeedRequest, FloodEmitRequest, DataGenerateRequest, TickRequest


def run_simulation() -> None:
    parser = argparse.ArgumentParser(description="GS-centric FANET simulator")
    parser.add_argument("--duration", type=int, default=60, help="Simulation duration in seconds")
    parser.add_argument("--tick-interval", type=float, default=2.0, help="Seconds between tick cycles")
    parser.add_argument("--flood-interval", type=float, default=10.0, help="Seconds between GS floods")
    parser.add_argument("--data-interval", type=float, default=5.0, help="Seconds between data bursts")
    parser.add_argument("--uav-count", type=int, default=12)
    parser.add_argument("--uav-prefix", type=str, default="UAV")
    parser.add_argument("--gs-id", type=str, default="GS-CORE")
    parser.add_argument("--neighbor-degree", type=int, default=2)
    parser.add_argument("--topology", type=str, default="ring")
    parser.add_argument("--sample-packets", type=int, default=4)
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()

    init_db()
    uav_ids = [f"{args.uav_prefix}-{i:02d}" for i in range(1, args.uav_count + 1)]

    with get_session() as session:
        seed_simulation(
            SimSeedRequest(
                gs_id=args.gs_id,
                uav_count=args.uav_count,
                uav_prefix=args.uav_prefix,
                neighbor_degree=args.neighbor_degree,
                topology=args.topology,
                reset=not args.no_reset,
                auto_flood=True,
                auto_data=True,
                sample_packets=args.sample_packets,
            ),
            session=session,
        )

    start = time.time()
    next_tick = start + args.tick_interval
    next_flood = start + args.flood_interval
    next_data = start + args.data_interval

    while time.time() - start < args.duration:
        now = time.time()
        with get_session() as session:
            if now >= next_flood:
                emit_flood(FloodEmitRequest(gs_id=args.gs_id), session=session)
                next_flood = now + args.flood_interval

            if now >= next_data:
                sample = random.sample(uav_ids, k=min(args.sample_packets, len(uav_ids)))
                for uav_id in sample:
                    send_data(
                        DataGenerateRequest(
                            source_uav_id=uav_id,
                            gs_id=args.gs_id,
                            payload_type="telemetry",
                            payload_size=128,
                            priority_level=PriorityLevel.STANDARD,
                            payload="sample",
                        ),
                        session=session,
                    )
                next_data = now + args.data_interval

            if now >= next_tick:
                tick(TickRequest(gs_id=args.gs_id), session=session)
                next_tick = now + args.tick_interval

        time.sleep(0.2)


if __name__ == "__main__":
    run_simulation()
