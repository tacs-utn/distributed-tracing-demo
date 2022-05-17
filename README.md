Distributed Tracing relying on a centralized Gateway Layer
=================

Example of several services routed by a centralized gateway layer.  It Includes:
- Decorator for adding the cluster description
- Custom Tags for adding meli general purpose headers.
- 2 gateways
	- gateway-frontends
	- gateway-backends: All the backend services will share the envoy service-cluster property, unlike the sidecars reporting distributedly the spans.  Collector's processors may correct it before send it to the backends.

Running
=======
Requirements
- docker compose
- curl

Step 1: Build the sandbox
1. `$ docker compose build && docker compose up -d`

Step 2: Generate some load
1. `$ curl -v localhost:8000/vip/MLA35553242 -H'x-myapp-trace-site:BR' -H'x-myapp-trace-bu:marketplace'`

Step 3: View the traces in Jaeger UI

Point your browser to http://localhost:16686 . You should see the Jaeger dashboard. Set the service to “frontend” and hit ‘Find Traces’. You should see traces from the gateway-frontends. Click on a trace to explore the path taken by the request from gateway-frontends to service1 to service2 through gateway-backends, as well as the latency incurred at each hop.

