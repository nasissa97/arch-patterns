import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers, Session

from orm import metadata, start_mappers

@pytest.fixture(scope="session")
def in_memory_db():
  start_mappers()
  engine = create_engine("sqlite:///:memory:")
  clear_mappers()
  return engine


@pytest.fixture(scope="function")
def setup_db(in_memory_db):
  metadata.create_all(bind=in_memory_db)
  yield
  metadata.drop_all(bind=in_memory_db)

@pytest.fixture(scope="function")
def session(in_memory_db, setup_db):
  Session = sessionmaker(bind=in_memory_db)
  session = Session()
  yield session
  session.close()

@pytest.fixture(scope="function")
def clear_db(session):
  for table in reversed(metadata.sorted_tables):
    session.execute(table.delete())
  session.commit()