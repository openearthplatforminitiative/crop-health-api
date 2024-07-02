# crop-health-api
API for crop health prediction. For more information check out the [developer portal](https://developer-test.openepi.io/data-catalog/crop-health/).

## Running locally

There are two docker images, one for TorchServe (which runs the models), and another image for FastAPI.

Start by creating a local network with docker, this will allow the containers to communicate with each other:
```
docker network create my-network
```

Now, in the `torch_serve/docker` folder, run one of the following to build the TorchServe image.
```
# For most CPUs
DOCKER_BUILDKIT=1 docker build --file Dockerfile -t pytorch/torchserve:latest-cpu --target production-image  ../

# For arm CPU
docker buildx build --platform=linux/amd64 --file Dockerfile -t pytorch/torchserve:latest-cpu --target production-image  ../
```
Then run the container:
```
docker run --rm -it --network my-network --name local_torchserve -p 8080:8080 -p 8081:8081 -p 8082:8082 pytorch/torchserve:latest-cpu
```

In the root of `crop-health-api`, run the following to build the FastAPI image:
```
docker build --file Dockerfile -t crop_fast_api ./
```
Then run the container:
```
docker run --rm -it --network my-network -p 127.0.0.1:5000:5000 crop_fast_api
```

Now requests can be sent to:
- http://localhost:8080/predictions/binary
- http://localhost:8080/predictions/single-HLT
- http://localhost:8080/predictions/multi-HLT

And the documentation can be found at:
- http://localhost:5000/redoc

Example request: `curl -X POST http://localhost:8080/predictions/binary -T cocoa.jpg`