from collections import Iterator
from itertools import cycle

from random_word import RandomWords


class RandomWordCycle:

    def __init__(self, word_pool_size: int = 500):
        random_words = RandomWords()
        random_word_list = []
        while not random_word_list:
            # Sometimes get_random_words() returns None. We'll try until it's not empty.
            random_word_list = random_words.get_random_words(limit=word_pool_size)
        self._word_cycle: Iterator[str] = cycle(random_word_list)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._word_cycle)
