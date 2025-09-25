from sqlalchemy import Table, Column, Integer, String, Float, Text
from .database import metadata

# notes 테이블
notes = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("content", String, nullable=False),
)

# recipes 테이블
recipes = Table(
    "recipes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rcp_seq", String, unique=True, nullable=False),
    Column("rcp_nm", String, nullable=False),
    Column("rcp_way2", String, nullable=False),
    Column("rcp_pat2", String, nullable=False),
    Column("info_eng", Float, nullable=False),
    Column("info_car", Float, nullable=False),
    Column("info_pro", Float, nullable=False),
    Column("info_fat", Float, nullable=False),
    Column("info_na", Float, nullable=False),
    Column("rcp_parts_dtls", Text, nullable=False),
    Column("recipe_steps", Text, nullable=False),
    Column("rcp_na_tip", Text, nullable=True),
    Column("hash_tag", Text, nullable=True),
)