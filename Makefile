up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose run --rm web python manage.py migrate

makemigrations:
	docker compose run --rm web python manage.py makemigrations

seed:
	docker compose run --rm web python manage.py seed_demo_data

test:
	docker compose run --rm web pytest -q

lint:
	docker compose run --rm web ruff check .
