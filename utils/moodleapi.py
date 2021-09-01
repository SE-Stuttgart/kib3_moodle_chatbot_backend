from utils.moodledb import Base, MLesson
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus as urlquote
from sqlalchemy.orm import sessionmaker

def connect_to_moodle_db(host='127.0.0.1', port=3306, user='moodle', pwd='m@0dl3ing', dbname='moodle'):
	print("connecting...")
	print(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4")
	engine = create_engine(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4", echo=True, future=True)
	conn = engine.connect()
	print("done")
	return engine, conn

# def get_lesson_pages(engine, conn):
# 	result = conn.execute(text("SELECT * FROM m_lesson_pages"))
# 	return result


engine, conn = connect_to_moodle_db()

# for row in get_lesson_pages(engine, conn):
# 	print("FOUND", row)


session = sessionmaker()
session.configure(bind=engine)
Base.metadata.create_all(engine)

for lesson in session.query(MLesson).all():
	print("Lesson", lesson)

conn.close()
