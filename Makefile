build:
	sudo docker build --tag web-kleber .

up:
	sudo docker save web-kleber | pv | ssh root sudo docker load

run:
	sudo docker-compose up