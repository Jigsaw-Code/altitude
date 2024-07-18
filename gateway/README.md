# Gateway

The Gateway is our application's reverse proxy, load balancer, and API gateway.
Its job is to sit between the outside world and the various services.

Currently it also serves our client frontend application (located under
`../client`) in a web server. In future, we may want to separate that out, but
for now we'll keep it simple.

## Running in a Docker container

Build a and run Docker image of the Gateway application:

```shell
docker build -t jigsaw/altitude-gateway .
docker run -p 8080:80 jigsaw/altitude-gateway
```

The Gateway will be serving on port `8080`, and the client web
application can be loaded at <http://localhost:8080>.
