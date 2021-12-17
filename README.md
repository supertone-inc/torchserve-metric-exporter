# TorchServe metric exporter
This module collects worker resources from TorchServe periodically and export as Prometheus format. An exported data 
could be collected by Prometheus server and used for monitoring TorchServe model worker if you make up dashboard on
Grafana.

**Metrics**:
* `ts_worker_cpu_usage`: TorchServe model worker CPU usage
* `ts_worker_memory_usage`: TorchServe model worker memory usage
* `ts_worker_memory_mib`: TorchServe model worker memory mebi-bytes

## How it works
* Get each of model worker information from TorchServe management API. This information includes PID, GPU usage and 
so on.
* Get additional information that not included in information (e.g. CPU percentage) from management API and append them
to previously gathered one. This is acquired by running process resource monitor command (e.g. `top` ) to TorchServe
server pod with K8s client.
* Expose data as Prometheus metrics.

## Apply to K8s cluster
This repository contains Kubernetes resources to deploy this service on Kubernetes cluster. 

Deployment could be done with Helm:
```shell
helm install ts-metric-exporter -n metric-exporter chart \
--set metric_exporter.namespace=metric-exporter \
--set torchserve.namespace=ns-ml-serve-c8cdbd7c \
--set torchserve.address=torchserve.ml-serve.svc.cluster.local
```

### Grafana Dashboard
Datasource `Prometheus` and `Loki` is required to get a TorchServe worker resource and request log by query. Each of 
service need to be installed and set on Datasource from Grafana configuration if not set before.

A sample grafana dashboard file is located at `grafana/torchserve_metric_dashboard.json`.
