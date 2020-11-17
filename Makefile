build:
	sudo docker build --tag web-kleber .

up:
	sudo docker save web-kleber | ssh root sudo docker load

run:
	sudo docker-compose up