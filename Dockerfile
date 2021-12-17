FROM python:3.9-alpine

ENV TS_METRIC_EXPORTER '/ts-metric-exporter'
RUN mkdir -p TS_METRIC_EXPORTER
WORKDIR $TS_METRIC_EXPORTER

COPY . .

RUN pip install -e .

ENTRYPOINT ["python3", "main.py"]