import asyncio
import json
import logging

from aioprometheus import Gauge

from ts_metric_exporter.k8s.pod import retrieve_target_pods
from ts_metric_exporter.ts import fetch_model_workers
from ts_metric_exporter.util.dictionary import extend_dict_by_match_key
from ts_metric_exporter.util.resource import (
    get_process_mem_usage,
    get_pod_process_resources_by_pid,
    LinuxTopProperties as Tp
)


async def _retrieve_ts_workers_resources(ts_management_api_url: str,
                                         ts_k8s_namespace: str,
                                         ts_pod_name) -> dict:
    """
    Retrieve TorchServe model worker resources.

    The PIDs from each of model workers could be retrieved with request to TorchServe management API.
    And fetch additional system resources that used by model worker from TorchServe server pod with matched PIDs.

    @param ts_management_api_url:
    @param ts_k8s_namespace:
    @param ts_pod_name:
    @return: Occupied system resource that used by TorchServe model worker.
    """
    model_workers_info = await fetch_model_workers(management_api_url=ts_management_api_url)
    model_worker_resources_raw = await get_pod_process_resources_by_pid(namespace=ts_k8s_namespace,
                                                                        pod_name=ts_pod_name,
                                                                        pids=model_workers_info.keys(),
                                                                        linux_top_props=(Tp.PID, Tp.CPU, Tp.RES))

    model_worker_resources = dict()

    model_worker_mem_usages = get_process_mem_usage(model_worker_resources_raw,
                                                    res_key_memory=Tp.RES.name.lower())

    for pid, mwrr in model_worker_resources_raw.items():
        mwrr_cpu, mwrr_res = mwrr['cpu'], mwrr['res']
        model_worker_resources[pid] = {
            'cpu_usage': mwrr_cpu,
            'mem_res_mib': mwrr_res / 1024
        }

    extend_dict_by_match_key(model_workers_info,
                             model_worker_resources,
                             model_worker_mem_usages)

    return model_workers_info


def _update_metric(ts_worker_metrics: dict[str, Gauge], ts_model_workers_resources: dict) -> None:
    """
    Update Prometheus metric values.

    In each of worker metrics (e.g. `cpu_usage`), model worker's resource value would be set with the label that
    helps distinguishing a model workers.

    @param ts_worker_metrics:
    @param ts_model_workers_resources:
    """
    curr_metric_labels = set()

    for pid, mw in ts_model_workers_resources.items():
        # Set model worker label.
        metric_label = {'model_name': mw['model_name'],
                        'model_version': mw['model_version'],
                        'pid': pid}
        metric_label_str = json.dumps(metric_label)
        curr_metric_labels.add(metric_label_str)

        for curr_worker_metric_key, curr_worker_metric in ts_worker_metrics.items():
            if metric_label_str not in curr_worker_metric.values.store:
                logging.debug(f'add data with label "{metric_label_str}" on "{curr_worker_metric.name}"')

            curr_worker_metric.set(labels=metric_label, value=mw[curr_worker_metric_key])

    for wm in ts_worker_metrics.values():
        prev_wm_labels = set(wm.values.store.keys()) ^ curr_metric_labels

        for pwl in prev_wm_labels:
            try:
                del wm.values.store[pwl]
                logging.debug(f'delete previous label "{pwl}" from "{wm.name}"')

            except KeyError:
                pass


async def get_ts_worker_resource(ts_server_address: str,
                                 ts_management_port: int,
                                 ts_k8s_namespace: str = 'torchserve',
                                 ts_k8s_pod_label_selector: str = 'app=torchserve',
                                 retrieve_duration_seconds: int = 10) -> None:
    """
    Retrieve TorchServe model worker resources and export these as Prometheus metrics.

    @param ts_server_address:
    @param ts_management_port:
    @param ts_k8s_namespace:
    @param ts_k8s_pod_label_selector: Used for select TorchServe server pod that matches label.
    @param retrieve_duration_seconds:
    """
    # Stores the value of worker resources in Prometheus metric instance.
    worker_metrics = {
        'cpu_usage': Gauge('ts_worker_cpu_usage', 'TorchServe model worker CPU usage'),
        'mem_usage': Gauge('ts_worker_memory_usage', 'TorchServe model worker memory usage'),
        'mem_res_mib': Gauge('ts_worker_memory_mib', 'TorchServe model worker memory mebi-bytes')
    }

    ts_management_api_url = ':'.join([ts_server_address, str(ts_management_port)])

    while True:
        ts_pod = await retrieve_target_pods(namespace=ts_k8s_namespace,
                                            label_selector=ts_k8s_pod_label_selector)
        ts_pod = ts_pod[0]

        ts_model_workers_resources = await _retrieve_ts_workers_resources(ts_k8s_namespace=ts_k8s_namespace,
                                                                          ts_pod_name=ts_pod,
                                                                          ts_management_api_url=ts_management_api_url)

        _update_metric(ts_worker_metrics=worker_metrics,
                       ts_model_workers_resources=ts_model_workers_resources)

        await asyncio.sleep(retrieve_duration_seconds)
