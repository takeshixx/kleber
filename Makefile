build:
	sudo docker build --tag web-kleber-dev .

build-amd64:
	sudo docker buildx build --platform linux/amd64 --tag web-kleber-dev .	

prod: build
	sudo docker build -f Dockerfile.prod --tag web-kleber .

prod-amd64:
	sudo docker buildx build --platform linux/amd64 -f Dockerfile.prod --tag web-kleber .

up:
	sudo docker save web-kleber | ssh root sudo docker load

up-prod: prod up

restart:
	ssh root "cd web; sudo docker-compose stop kleber; sudo docker-compose up -d kleber"

run:
	sudo docker-compose up
