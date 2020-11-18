build:
	sudo docker build --tag web-kleber-dev .

prod: build
	sudo docker build -f Dockerfile.prod --tag web-kleber .

up:
	sudo docker save web-kleber | pv | ssh root sudo docker load

up-prod: prod up

run:
	sudo docker-compose up