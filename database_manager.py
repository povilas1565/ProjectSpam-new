from sqlmodel import Session, create_engine, SQLModel, select
from loguru import logger
from models.database import *
import settings
import urllib


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DatabaseManager(metaclass=Singleton):
    def __init__(self):
        sqlite_url = f"sqlite:///{settings.DATABASE_PATH}/database.db"
        self._engine = create_engine(sqlite_url)
        SQLModel.metadata.create_all(self._engine)

    def is_exist(self, model, statement) -> bool:
        try:
            with Session(self._engine) as session:
                session.expire_on_commit = False
                result = session.exec(select(model).where(statement)).first()
                if result:
                    return True
        except Exception as e:
            logger.error(f"Error happened: {e}")
        return False

    def read_data(self, model, statement=None, all_data: bool = False):
        try:
            with Session(self._engine) as session:
                session.expire_on_commit = False
                if statement is not None:
                    if not all_data:
                        result = session.exec(select(model).where(statement)).first()
                    else:
                        result = session.exec(select(model).where(statement)).all()
                    return result
                else:
                    query = select(model)
                    res = session.execute(query)
                    items = res.scalars().all()
                    return items
        except Exception as e:
            logger.error(f"Error happened: {e}")
        return None

    def save_data(self, model):
        try:
            with Session(self._engine) as session:
                session.expire_on_commit = False
                session.add(model)
                session.commit()
                session.refresh(model)
            logger.success(f"{model} saved to databse")

            return model

        except Exception as e:
            logger.error(f"Error happened: {e}")

        return None

    def remove_data(self, model, statement):
        try:
            with Session(self._engine) as session:
                session.expire_on_commit = False
                result = session.exec(select(model).where(statement)).first()
                session.delete(result)
                session.commit()
                return result
        except Exception as e:
            logger.error(f"Error happened: {e}")
        return None

