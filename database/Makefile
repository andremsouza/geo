# Builds and run docker container from Dockerfile
build:
	docker build -t geo_postgresql .
run:
	docker run -P --name geo geo_postgresql
run_tmp:
	docker run -P --rm --name geo geo_postgresql

terminal:
	docker exec -it geo bash
