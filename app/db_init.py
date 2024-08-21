from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("mysql+aiomysql://enemy:root@mysql_db/project")

AsyncSessionLocal = sessionmaker(class_=AsyncSession, autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()



