from flask import Flask
from flask import request
import os
import requests
import socket
import sys

from opentelemetry import trace, propagate
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import ( OTLPSpanExporter,
)
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


app = Flask(__name__)

resource = Resource.create(attributes={"service.name": os.environ['SERVICE_NAME']})

trace.set_tracer_provider(TracerProvider(resource=resource))
propagate.set_global_textmap(B3MultiFormat())

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel:4317", insecure=True))
)

RequestsInstrumentor().instrument()
FlaskInstrumentor().instrument_app(app)

tracer = trace.get_tracer(__name__)

TRACE_HEADERS_TO_PROPAGATE = [
    'X-Ot-Span-Context',
    'X-Request-Id',

    # Zipkin headers
    #'X-B3-TraceId',
    #'X-B3-SpanId',
    #'X-B3-ParentSpanId',
    #'X-B3-Sampled',
    #'X-B3-Flags',

    # Jaeger header (for native client)
    "uber-trace-id",

    # SkyWalking headers.
    "sw8",

    # generic purpose myapp's headers.  It should be replaced by baggage feature
    "x-myapp-trace-site",
    "x-myapp-trace-bu"
]


@app.route('/vip/<itemId>')
def vipEndpoint(itemId):
    headers = {}

    # call service 2 from service 1
    if os.environ['SERVICE_NAME'] == "shops.web-vip":
        for header in TRACE_HEADERS_TO_PROPAGATE:
            if header in request.headers:
                headers[header] = request.headers[header]
        requests.get("http://gateway-backends:9000/middleend/" + itemId, headers=headers)

    return (
        'Hello from behind Envoy (service {})! item: {} hostname: {} resolved'
        'hostname: {}\n'.format(
            os.environ['SERVICE_NAME'], 
            itemId,
            socket.gethostname(),
            socket.gethostbyname(socket.gethostname())))


@app.route('/middleend/<itemId>')
def middleendEndpoint(itemId):
    with tracer.start_as_current_span("internal_middleend_work") as internal_span:
        headers = {}

        # call service 3 from service 2
        if os.environ['SERVICE_NAME'] == "read.items-middleend":
            for header in TRACE_HEADERS_TO_PROPAGATE:
                if header in request.headers:
                    headers[header] = request.headers[header]
            internal_span.add_event("hello from my internal span", {"x":123})
            requests.get("http://gateway-backends:9000/items/" + itemId, headers=headers)

    with tracer.start_as_current_span("return_stuff"):
        return (
            'Hello from behind Envoy (service {})! item: {} hostname: {} resolved'
            'hostname: {}\n'.format(
                os.environ['SERVICE_NAME'], 
                itemId,
                socket.gethostname(),
                socket.gethostbyname(socket.gethostname())))


@app.route('/items/<itemId>')
def backendEndpoint(itemId):
    headers = {}
    return (
        'Hello from behind Envoy (service {})! item: {} hostname: {} resolved'
        'hostname: {}\n'.format(
            os.environ['SERVICE_NAME'], 
            itemId,
            socket.gethostname(),
            socket.gethostbyname(socket.gethostname())))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
