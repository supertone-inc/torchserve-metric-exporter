from kubernetes import config
from kubernetes.config import ConfigException

try:
    config.load_incluster_config()

except ConfigException as e:
    try:
        config.load_kube_config()

    except Exception as e:
        print(e)
