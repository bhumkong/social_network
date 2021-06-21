import databases
import sqlalchemy as sql

metadata = sql.MetaData()
DATABASE_URL = 'postgresql:///social_network'
database = databases.Database(DATABASE_URL)


user_table = sql.Table(
    'app_user',
    metadata,
    sql.Column('id', sql.Integer, primary_key=True),
    sql.Column('username', sql.String, nullable=False, unique=True),
    sql.Column('password_hash', sql.String),
    sql.Column('last_visit', sql.DateTime),
    sql.Column('last_login', sql.DateTime),
)

post_table = sql.Table(
    'post',
    metadata,
    sql.Column('id', sql.Integer, primary_key=True),
    sql.Column('author_id', sql.Integer, sql.ForeignKey('app_user.id', ondelete='CASCADE'), nullable=False),
    sql.Column('title', sql.String, nullable=False, unique=True),
    sql.Column('body', sql.String, nullable=False),
)

like_table = sql.Table(
    'user_like_post',
    metadata,
    sql.Column('user_id', sql.Integer, sql.ForeignKey('app_user.id', ondelete='CASCADE'), primary_key=True),
    sql.Column('post_id', sql.Integer, sql.ForeignKey('post.id', ondelete='CASCADE'), primary_key=True),
    sql.Column('datetime', sql.DateTime, server_default=sql.func.statement_timestamp(), nullable=False),
)
