build:
	sudo docker build --tag web-kleber-dev .

prod: build
	sudo docker build -f Dockerfile.prod --tag web-kleber .

up:
	sudo docker save web-kleber | pv | ssh root sudo docker load

up-prod: prod up

restart:
	ssh root "cd web; sudo docker-compose stop kleber; sudo docker-compose up -d kleber"

run:
	sudo docker-compose up