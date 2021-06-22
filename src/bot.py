import json
import os
import random
from typing import Iterator, Optional

import requests
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

from src.random_words import RandomWordCycle


class Bot:
    _word_cycle: Iterator[str]
    _number_of_users: int
    _max_posts_per_user: int
    _max_likes_per_user: int
    MIN_WORDS_IN_POST = 2
    MAX_WORDS_IN_POST = 12

    def __init__(
            self,
            *,
            number_of_users: Optional[int] = None,
            max_posts_per_user: Optional[int] = None,
            max_likes_per_user: Optional[int] = None,
    ):
        self._number_of_users = number_of_users
        self._max_posts_per_user = max_posts_per_user
        self._max_likes_per_user = max_likes_per_user
        self._word_cycle = RandomWordCycle()

    def read_config_from_file(self, file_path):
        """ Loads config from file, overwriting current values. """
        with open(file_path) as json_file:
            data = json.load(json_file)
        self._number_of_users = data.get('number_of_users')
        self._max_posts_per_user = data.get('max_posts_per_user')
        self._max_likes_per_user = data.get('max_likes_per_user')

    def create_users(self) -> list[tuple[str, str]]:
        """
        Registers users.

        Returns:
            List of (username, password) tuples for successfully created users.
        """
        assert self._number_of_users
        url = 'http://localhost:8000/api/users/'
        credentials = []
        for _ in range(self._number_of_users):
            username, password = next(self._word_cycle), next(self._word_cycle)
            body = {'username': username, 'password': password}
            response = requests.post(url, json=body)
            if response.status_code == 200:
                print(f'Created user {username}')
                credentials.append((username, password))
            else:
                print(f'Could not create user {username}')
        return credentials

    def log_in_users(self, users_credentials: list[tuple[str, str]]) -> list[dict[str, str]]:
        """
        Signs in users.

        Args:
            users_credentials: List of (username, password) tuples.

        Returns:
            List of successfully retrieved tokens.
        """
        token_list = []
        for user, password in users_credentials:
            token = self.log_in_user(user, password)
            if token:
                token_list.append(token)
        return token_list

    def log_in_user(self, username: str, password: str) -> Optional[dict[str, str]]:
        """ Logs in user, returning auth token or None if could not create. """
        url = 'http://localhost:8000/token/'
        oauth = OAuth2Session(client=LegacyApplicationClient(client_id=''))
        try:
            token = oauth.fetch_token(token_url=url, username=username, password=password)
        except Exception:
            token = None
            print(f'Could not log in user {username}')
        else:
            print(f'Logged in user {username}')
        return token

    def get_auth_headers(self, user_token: dict[str, str]) -> dict[str, str]:
        """ Transform token date to use in requests. """
        token_type = user_token['token_type']
        access_token = user_token['access_token']
        headers = {
            'Authorization': f'{token_type} {access_token}'
        }
        return headers

    def create_post(self, auth_headers) -> Optional[int]:
        """ Creates post, returning post_id or None if could not create. """
        url = 'http://localhost:8000/api/posts/'
        title = next(self._word_cycle)
        number_of_words_in_body = random.randrange(self.MIN_WORDS_IN_POST, self.MAX_WORDS_IN_POST + 1)
        body = ' '.join(next(self._word_cycle) for _ in range(number_of_words_in_body))
        response = requests.post(url, headers=auth_headers, json={'title': title, 'body': body})
        if response.status_code == 200:
            print(f'Created post "{title}"')
            return response.json()['id']
        else:
            print(f'Could not create post "{title}"')

    def create_posts(self, auth_headers_list) -> list[int]:
        assert self._max_posts_per_user
        post_id_list = []
        for user_auth_headers in auth_headers_list:
            number_of_posts = random.randrange(1, self._max_posts_per_user + 1)
            for _ in range(number_of_posts):
                post_id = self.create_post(user_auth_headers)
                if post_id is not None:
                    post_id_list.append(post_id)
        return post_id_list

    def like_post(self, post_id: int, auth_headers):
        url = f'http://localhost:8000/api/posts/{post_id}/like/'
        response = requests.post(url, headers=auth_headers)
        if response.status_code == 200:
            print(f'Liked post {post_id}')
        else:
            print(f'Could not like post {post_id}')

    def like_posts(self, auth_headers_list, post_id_list):
        assert self._max_likes_per_user
        for user_auth_headers in auth_headers_list:
            number_of_likes = random.randrange(1, self._max_likes_per_user + 1)
            number_of_likes = min(number_of_likes, len(post_id_list))
            post_ids_to_like = random.sample(post_id_list, number_of_likes)
            for post_id in post_ids_to_like:
                self.like_post(post_id, user_auth_headers)

    def run_actions(self):
        user_credentials_list: list[tuple[str, str]] = self.create_users()
        tokens = self.log_in_users(user_credentials_list)
        auth_headers_list = [self.get_auth_headers(token) for token in tokens]
        post_id_list = self.create_posts(auth_headers_list)
        self.like_posts(auth_headers_list, post_id_list)


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    bot = Bot()
    bot.read_config_from_file('bot_config.json')
    bot.run_actions()
