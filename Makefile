.PHONY: build
build:
	sudo docker build --tag kleber-dev-arm64 .

.PHONY: build-amd64
build-amd64:
	sudo docker buildx build --platform linux/amd64 --tag web-kleber-dev .	

.PHONY: prod
prod: build
	sudo docker build -f Dockerfile.prod --tag kleber-arm64 .

.PHONY: prod-amd64
prod-amd64: build-amd64
	sudo docker buildx build --platform linux/amd64 -f Dockerfile.prod --tag web-kleber .

.PHONY: up
up:
	sudo docker save web-kleber | ssh root sudo docker load

.PHONY: up-prod
up-prod: prod up

.PHONY: restart
restart:
	ssh root "cd web; sudo docker-compose stop kleber; sudo docker-compose up -d kleber"

.PHONY: stop
stop:
	docker-compose down

.PHONY: run
run: stop
	docker-compose up -d