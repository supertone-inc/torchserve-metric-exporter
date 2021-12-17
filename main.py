import logging

import asyncio
from aioprometheus.service import Service

from ts_metric_exporter.collector.worker_resource import get_ts_worker_resource


async def main(exporter_address: str, 
               exporter_port: int, 
               ts_address: str, 
               ts_management_port: int,
               refresh_duration_seconds: int,
               ts_k8s_namespace: str) -> None:
    """
    Launches Prometheus exporter service.

    This runs:
        - exportation of TorchServe model worker resources as Prometheus metrics.

    @param exporter_address: An address to accept on exposed exporter service.
    @param exporter_port: An port to accept on exposed exporter service.
    @param ts_address:
    @param ts_management_port:
    @param refresh_duration_seconds:
    @param ts_k8s_namespace:
    """
    service = Service()

    await service.start(addr=exporter_address, port=exporter_port)
    logging.info(f'Serving TorchServe resource exporter on "{service.metrics_url}"')
    
    await get_ts_worker_resource(ts_server_address=ts_address,
                                 ts_management_port=ts_management_port,
                                 ts_k8s_namespace=ts_k8s_namespace,
                                 retrieve_duration_seconds=refresh_duration_seconds)

    await service.stop()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--exporter-address', type=str, default='0.0.0.0', required=False)
    parser.add_argument('--exporter-port', type=int, default=8082, required=False)
    parser.add_argument('--ts-address', type=str, default='127.0.0.1', required=True)
    parser.add_argument('--ts-management-port', type=int, default=8081, required=False)
    parser.add_argument('--refresh-duration-seconds', type=int, default=10, required=False)
    parser.add_argument('--ts-k8s-namespace', type=str, default='torchserve', required=False)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main(exporter_address=args.exporter_address,
                         exporter_port=args.exporter_port,
                         ts_address=args.ts_address,
                         ts_management_port=args.ts_management_port,
                         refresh_duration_seconds=args.refresh_duration_seconds,
                         ts_k8s_namespace=args.ts_k8s_namespace))

    except KeyboardInterrupt:
        pass
