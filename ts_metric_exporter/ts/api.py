import requests
from requests.adapters import HTTPAdapter, Retry

from ts_metric_exporter.util import key_as_underscore


async def fetch_model_workers(management_api_url: str) -> dict:
    """
    Retrieve model workers information from TorchServe management API.

    @param management_api_url:
    @return: TorchServe model worker information.
    """
    model_workers = dict()

    with requests.Session() as sess:
        retries_num = 5
        backoff_factor = 0.3
        status_forcelist = (500, 502, 504)

        retry = Retry(
            total=retries_num,
            read=retries_num,
            connect=retries_num,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist
        )

        req_adapter = HTTPAdapter(max_retries=retry)

        sess.mount('http://', req_adapter)

        models_info = sess.get(f'http://{management_api_url}/models').json()['models']
        for mi in models_info:
            model_name, _ = mi.values()
            registered_models_in_model_name = sess.get(f'http://{management_api_url}/models/{model_name}').json()
            for rm in registered_models_in_model_name:
                rm = key_as_underscore(rm)
                curr_registered_model_workers = {item['pid']: {'model_name': rm['model_name'],
                                                               'model_version': rm['model_version'],
                                                               'sock_id': item['id'],
                                                               'gpu_usage': item['gpu_usage']
                                                               if item['gpu_usage'] != 'N/A' else None}
                                                 for item in key_as_underscore(rm['workers'])}

                model_workers.update(curr_registered_model_workers)

    return model_workers
