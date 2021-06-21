from collections import defaultdict
from datetime import date, datetime
from typing import Optional

from asyncpg import UniqueViolationError, ForeignKeyViolationError
from dateutil import rrule
from sqlalchemy import cast, Date, select, func, sql

from db_schema import post_table, database, user_table, like_table
from models import Post, UserAuth, User, RowCreationResult


async def insert_user(username: str, password_hash: str) -> bool:
    query = user_table.insert().values(username=username, password_hash=password_hash)
    try:
        await database.execute(query)
    except UniqueViolationError:
        return False
    return True


async def insert_post(author_id: int, title: str, body: str) -> Optional[int]:
    query = post_table.insert().values(author_id=author_id, title=title, body=body)
    try:
        post_id = await database.execute(query)
    except UniqueViolationError:
        return None
    return post_id


async def select_posts(post_ids: list[int] = None) -> list[Post]:
    query = post_table.join(user_table).select().with_only_columns([
        post_table.c.id,
        post_table.c.title,
        post_table.c.body,
        user_table.c.id,
        user_table.c.username,
        user_table.c.last_visit,
        user_table.c.last_login,
    ]).order_by(post_table.c.id)
    if post_ids is not None:
        query = query.where(post_table.c.id.in_(post_ids))
    results = await database.fetch_all(query)

    def get_post_from_row(row) -> Post:
        return Post(
            id=row[0],
            title=row[1],
            body=row[2],
            author=User(
                id=row[3],
                username=row[4],
                last_visit=row[5],
                last_login=row[6],
            ),
            like_count=post_like_map[row[0]],
        )

    post_like_map = await get_posts_like_count()

    return [get_post_from_row(row) for row in results]


async def get_posts_like_count() -> defaultdict[int, int]:
    query = select([
        like_table.c.post_id,
        func.count(like_table.c.user_id).label('count'),
    ]).group_by(
        like_table.c.post_id,
    )
    rows = await database.fetch_all(query)
    post_like_map = defaultdict(int)
    for row in rows:
        post_like_map[row['post_id']] = row['count']
    return post_like_map


async def get_post_like_count(post_id: int) -> int:
    query = like_table.count().where(like_table.c.post_id == post_id)
    like_count = await database.execute(query)
    return like_count


async def fetch_user(username: str) -> Optional[UserAuth]:
    query = user_table.select().where(user_table.c.username == username)
    user_dict = await database.fetch_one(query)
    if user_dict:
        return UserAuth(**user_dict)


async def fetch_users() -> list[UserAuth]:
    query = user_table.select().order_by(user_table.c.id)
    rows = await database.fetch_all(query)
    return [UserAuth(**row) for row in rows]


async def create_like(user_id: int, post_id: int) -> RowCreationResult:
    query = like_table.insert().values(user_id=user_id, post_id=post_id)
    try:
        await database.execute(query)
    except UniqueViolationError:
        return RowCreationResult.UNIQUE_VIOLATION
    except ForeignKeyViolationError:
        return RowCreationResult.FOREIGN_KEY_VIOLATION
    return RowCreationResult.CREATED


async def delete_like(user_id: int, post_id: int) -> bool:
    """ Returns True if like was deleted, False otherwise (when like not existed). """
    query = like_table.delete(returning=[like_table.c.user_id]).where(
        like_table.c.user_id == user_id,
    ).where(
        like_table.c.post_id == post_id,
    )
    result = await database.execute(query)
    if result is None:
        return False
    return True


async def update_last_visit(user_id: int) -> None:
    query = user_table.update().values(
        last_visit=datetime.now(),
    ).where(user_table.c.id == user_id)
    await database.execute(query)


async def update_last_login(user_id: int) -> None:
    query = user_table.update().values(
        last_login=datetime.now(),
    ).where(user_table.c.id == user_id)
    await database.execute(query)


async def get_like_stats(date_from: date, date_to: date) -> dict[date, dict]:
    like_date = cast(like_table.c.datetime, Date).label('date')
    query = select([
        like_date,
        like_table.c.post_id,
        func.count(like_table.c.user_id).label('count'),
    ]).where(
        sql.and_(
            like_date >= date_from,
            like_date <= date_to,
        )
    ).group_by(
        like_date,
        like_table.c.post_id,
    ).order_by(
        like_date,
        like_table.c.post_id,
    )
    rows = await database.fetch_all(query)

    result: dict[date, dict] = {}
    all_dates = rrule.rrule(rrule.DAILY, dtstart=date_from, until=date_to)
    for date_time in all_dates:
        result[date_time.date()] = {}
    for row in rows:
        result[row['date']][row['post_id']] = row['count']
    for day_likes in result.values():
        day_likes['total'] = sum(day_likes.values())

    return result
