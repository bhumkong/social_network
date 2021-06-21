## Basic "social network" API + bot to test it out

##### Tech used: FastAPI, SQLAlchemy Core + databases, PostgreSQL.

How to try it:
1. Create python environment
    1. Configure venv with python 3.9+ and activate it
    2. Install python-poetry if you don't have it
    3. Run `poetry install` to install dependencies
2. Prepare database
    1. Create postgres database
    2. Write your db connection string to `DATABASE_URL` variable in `src/db_schema.py`
    3. Write the same string to `sqlalchemy.url` variable in `alembic.ini`
    4. Run `alembic upgrade head` to create sql tables
3. Run the server with `python src/main.py`
4. Explore the API at http://127.0.0.1:8000/docs#/
    * Some endpoints require authentication. To use them, first create your user with POST `/api/users/`, filling in `username` and `password` json parameters. Then click "Authorize" button, fill your `username` and `password` in the form and proceed. If you are successfully authorized, you'll be able to use all the endpoints.
5. Run the bot
    * You can set bot configuration parameters in `bot_config.json` file
    * Run the bot with `python src/bot.py`
    * What the bot does:
      * Create `number_of_users` users
      * Authenticate these users (get tokens)
      * Create a random number of posts (up to `max_posts_per_user`) for each created user
      * Like a random number of posts (up to `max_likes_per_user`) for each created user
    * Notes:
      * Random word generation is quite slow, so it takes a few seconds to initialize the bot

### Interactive API docs:

![API docs screenshot](https://raw.githubusercontent.com/bhumkong/social_network/master/api.png)
