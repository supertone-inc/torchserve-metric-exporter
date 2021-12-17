from enum import IntEnum

from ts_metric_exporter.k8s.pod import exec_command_to_pod


class LinuxTopProperties(IntEnum):
    PID = 1
    USER = 2
    PR = 3
    NI = 4
    VIRT = 5
    RES = 6
    SHR = 7
    S = 8
    CPU = 9
    MEM = 10
    TIME = 11
    COMMAND = 12


get_linux_top_props_cast_fn = {
    'pid': lambda item: int(item),
    'user': lambda item: str(item),
    'pr': lambda item: int(item),
    'ni': lambda item: int(item),
    'virt': lambda item: int(item),
    'res': lambda item: int(item),
    'shr': lambda item: int(item),
    's': lambda item: str(item),
    'cpu': lambda item: float(item),
    'mem': lambda item: float(item),
    'time': lambda item: str(item),
    'command': lambda item: str(item)
}


def get_process_mem_usage(processes_resources: dict[int, dict],
                          res_key_memory: str = 'mem_res_kib') -> dict:
    """
    Return processes memory usage among `processes_resources` as percentage.

    @param processes_resources:
    @param res_key_memory: Key of memory resource from `process_resources`.
    @return: process memory usage displayed as percentage.
    """
    mem_res_total = sum([item[res_key_memory]
                         for item in processes_resources.values()])
    process_mem_usages = {pid: {'mem_usage': (res[res_key_memory] / mem_res_total) * 100}
                          for pid, res in processes_resources.items()}

    return process_mem_usages


def get_process_resources_by_pid_cmd(pids: list[int], top_properties: tuple[LinuxTopProperties, ...]) -> list[str]:
    """
    Returns command that catches process system resources.

    @param pids: Filters processes from result of linux `top`.
    @param top_properties: Items to filter result from linux `top`.
    @return: Command list that executable on K8s client.
    """
    top_pids_str = ','.join([str(item) for item in pids])
    top_awk_str = f"{{ print {','.join(['$' + str(int(item)) for item in top_properties])} }}"
    process_resource_command = [
        "/bin/sh",
        "-c",
        f"top -b -n 2 -d 0.2 -p {top_pids_str} | "
        f"tail -n -{len(pids)} | "
        f"awk '{top_awk_str}'"
    ]

    return process_resource_command


async def get_pod_process_resources_by_pid(namespace: str,
                                           pod_name: str,
                                           pids: list[int],
                                           linux_top_props: tuple[LinuxTopProperties, ...]) -> dict[dict]:
    """
    Retrieve process resources from K8s pod.

    @param namespace:
    @param pod_name:
    @param pids:
    @param linux_top_props: Items to filter at linux `top`.
    @return: Process resources.
    """
    if len(pids) == 0:
        return {}

    process_resources_by_pid_cmd = get_process_resources_by_pid_cmd(pids, linux_top_props)
    # Executes resource fetch command to K8s pod and save its result.
    worker_resource_raw = await exec_command_to_pod(namespace=namespace,
                                                    pod_name=pod_name,
                                                    command=process_resources_by_pid_cmd)
    process_resources = dict()
    linux_top_props_str = [item.name.lower() for item in linux_top_props]
    # Parse line of process resources, with type-casting and save as dict.
    for wr_raw_line in worker_resource_raw.split('\n')[:-1]:
        wr_raw_res = wr_raw_line.split()
        curr_process_res = {k: get_linux_top_props_cast_fn.get(k)(v)
                            for k, v in zip(linux_top_props_str, wr_raw_res)}
        process_resources[curr_process_res['pid']] = curr_process_res

    return process_resources
