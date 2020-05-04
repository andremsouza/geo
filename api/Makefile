build:
	docker build -t geo_api .
run:
	docker run -P --env-file env.list -it --name geo_api geo_api
run_tmp:
	docker run -P --rm --env-file env.list -it --network=host --name geo_api geo_api
terminal:
	docker exec -it geo_api bash
