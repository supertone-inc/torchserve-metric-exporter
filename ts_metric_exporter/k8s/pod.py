from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream


async def retrieve_target_pods(namespace: str, label_selector: str) -> list:
    """
    Retrieve K8s pod names that matches namespace and label.

    @param namespace:
    @param label_selector:
    @return: pod names that matches conditions.
    """
    pod_info = core_v1_api.CoreV1Api().list_namespaced_pod(namespace=namespace,
                                                           label_selector=label_selector)
    
    return [item.metadata.name for item in pod_info.items]


async def exec_command_to_pod(namespace: str, pod_name: str, command: list[str]) -> stream:
    """
    Run command to K8s pod and get results.

    @param namespace:
    @param pod_name:
    @param command:
    @return:
    """
    return stream(core_v1_api.CoreV1Api().connect_get_namespaced_pod_exec,
                  namespace=namespace,
                  name=pod_name,
                  command=command,
                  stderr=True,
                  stdin=False,
                  stdout=True,
                  tty=False)
