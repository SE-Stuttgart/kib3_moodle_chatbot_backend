
# coding: utf-8
from sqlalchemy import Column, DECIMAL, String, text, create_engine
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT, TINYINT
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus as urlquote
from sqlalchemy.orm import relationship, sessionmaker
import datetime
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.types import TypeDecorator


Base = declarative_base()
metadata = Base.metadata

class UnixTimestamp(TypeDecorator):
	impl = BIGINT

	def process_bind_param(self, value, dialect):
		return value.replace(tzinfo=datetime.timezone.utc).timestamp()

	def process_result_value(self, value, dialect):
		return datetime.datetime.utcfromtimestamp(value)

class Sequence(TypeDecorator):
	impl = LONGTEXT

	def process_bind_param(self, value, dialect):
		return ",".join(value)

	def process_result_value(self, value, dialect):
		return value.split(",")

class CompletionState(TypeDecorator):
	impl = TINYINT

	def process_bind_param(self, value, dialect):
		return 1 if value else 0

	def process_result_value(self, value, dialect):
		return value > 0

def connect_to_moodle_db(host='127.0.0.1', port=3306, user='moodle', pwd='m@0dl3ing', dbname='moodle'):
	print("connecting...")
	print(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4")
	engine = create_engine(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4", echo=False, future=True)
	conn = engine.connect()
	print("done")
	return engine, conn


class MGradeGradesHistory(Base):
	__tablename__ = 'm_grade_grades_history'

	id = Column(BIGINT(10), primary_key=True)
	# action = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'")) # created/modified/deleted constants
	oldid = Column(BIGINT(10), nullable=False, index=True) # old or current MGradeGrade.id 

	timemodified = Column(UnixTimestamp, index=True)

	rawgrade = Column(DECIMAL(10, 5))
	rawgrademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
	rawgrademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
	finalgrade = Column(DECIMAL(10, 5))

	# loggeduser = Column(BIGINT(10), index=True)
	_grateItemid = Column(BIGINT(10), ForeignKey("MGradeItem.id"), nullable=False, index=True, name="itemid")
	_userid = Column(BIGINT(10), ForeignKey("MUser.id"), nullable=False, index=True, name="userid")

	def get_grade_item(self):
		session = Session.object_session(self)
		return session.query(MGradeItem).get(self._gradeItemId)

	def get_user(self):
		session = Session.object_session(self)
		return session.query(MGradeItem).get(self._gradeItemId)

	def __repr__(self) -> str:
		return f"Grade {self.get_grade_item().itemname} for User {self.get_user().username}: {self.finalgrade}"


class MGradeGrade(Base):
	"""
	Access user via MGradeGrade.user
	Access grade item via MGradeGrade.gradeItem
	"""
	__tablename__ = 'm_grade_grades'

	id = Column(BIGINT(10), primary_key=True)
	rawgrade = Column(DECIMAL(10, 5))
	rawgrademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
	rawgrademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
	finalgrade = Column(DECIMAL(10, 5))

	# timecreated = Column(UnixTimestamp)
	# timemodified = Column(UnixTimestamp)
	
	# aggregationstatus = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("'unknown'"))
	# aggregationweight = Column(DECIMAL(10, 5))

	_userid = Column(BIGINT(10), ForeignKey("MUser.id"), nullable=False, index=True, name="userid")
	_gradeItemId = Column(BIGINT(10), ForeignKey("MGradeItem.id"), nullable=False, index=True, name="itemid")
	
	def get_grade_item(self):
		session = Session.object_session(self)
		return session.query(MGradeItem).get(self._gradeItemId)

	def get_user(self):
		session = Session.object_session(self)
		return session.query(MGradeItem).get(self._gradeItemId)

	def __repr__(self) -> str:
		return f"Grade {self.get_grade_item().itemname} for User {self.get_user().username}: {self.finalgrade}"


class MGradeItem(Base):
	" Access course via MGradeItem.course " 
	__tablename__ = 'm_grade_items'

	id = Column(BIGINT(10), primary_key=True)
	itemname = Column(String(255, 'utf8mb4_bin'))

	itemtype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	itemmodule = Column(String(30, 'utf8mb4_bin'))

	grademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
	grademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))

	timecreated = Column(UnixTimestamp)
	timemodified = Column(UnixTimestamp)

	# categoryid = Column(BIGINT(10), index=True)
	_courseid = Column(BIGINT(10), ForeignKey('m_course.id'), index=True, name='courseid')

	# def __repr__(self) -> str:
	# 	return f"""Grade Item: {self.itemname}, Current grades: {self.grades}"""


class MUserLastacces(Base):
	__tablename__ = 'm_user_lastaccess'

	id = Column(BIGINT(10), primary_key=True)
	timeaccess = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	user = relationship("MUser", back_populates="last_accessed_course", uselist=False)
	course = relationship("MCourse", back_populates="", uselist=False)

	_courseid = Column(BIGINT(10), ForeignKey('m_course.id'), nullable=False, index=True, server_default=text("'0'"), name='courseid')
	_userid = Column(BIGINT(10), ForeignKey('m_user.id'), nullable=False, index=True, server_default=text("'0'"), name='userid')

	def __repr__(self) -> str:
		return f"Last Access from user {self._userid} to Course {self._courseid} on {self.timeaccess}"


class MUser(Base):
	__tablename__ = 'm_user'

	id = Column(BIGINT(10), primary_key=True)
	username = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	idnumber = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
	firstname = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
	middlename = Column(String(255, 'utf8mb4_bin'), index=True)
	lastname = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
	alternatename = Column(String(255, 'utf8mb4_bin'), index=True)

	firstaccess = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
	lastaccess = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))

	lastlogin = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
	currentlogin = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	# trackforums = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
	timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
	timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	last_accessed_course = relationship("MUserLastacces", back_populates="user", uselist=False)

	def get_grades(self):
		session = Session.object_session(self)
		return session.query(MGradeGrade).filter(MGradeGrade._userid==self.id).all()

	def get_grade_history(self):
		session = Session.object_session(self)
		return session.query(MGradeGradesHistory).filter(MGradeGradesHistory._userid==self.id).all()

	def get_completed_courses(self):
		session = Session.object_session(self)
		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True)
		return [completion.coursemodule for completion in completions]

	def get_last_completed_coursemodule(self):
		session = Session.object_session(self)
		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True).all()
		if len(completions) == 0:
			return None
		return max(completions, key=lambda comp: comp.timemodified)

	def get_last_accessed_coursmodule(self):
		pass

	def get_open_coursemodules(self):
		pass

	def get_grades(self):
		session = Session.object_session(self)
		return session.query(MGradeGrade).filter(MGradeGrade._userid==self.id).all()

	def __repr__(self) -> str:
		print("T", 	type(self.last_accessed_course))
		return f"""User {self.username} ({self.id})
			- Last login: {self.lastlogin}
			- Last accessed course: {self.last_accessed_course.course.fullname}
			- Grades: {self.get_grades()}
		"""

class MCourseModulesCompletion(Base):
	# parent courseodule: MCourseModulesCompletion.coursemodule
	__tablename__ = 'm_course_modules_completion'

	id = Column(BIGINT(10), primary_key=True)
	completed = Column(CompletionState, nullable=False, name='completionstate')
	timemodified = Column(UnixTimestamp, nullable=False)

	_coursemoduleid = Column(BIGINT(10), ForeignKey("m_course_modules.id"), nullable=False, index=True, name="coursemoduleid")
	_userid = Column(BIGINT(10), ForeignKey("m_user.id"), nullable=False, name="userid") # TODO relation to user

	def __repr__(self) -> str:
		return f"Completion: course_module_id {self._coursemoduleid}: {self.completed} for user {self._userid}"


class MCourseModule(Base):
	# parent course: MCourseModule.course
	# parent section: MCourseModule.section
	__tablename__ = 'm_course_modules'

	id = Column(BIGINT(10), primary_key=True)
	# TODO module = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'")) 
	added = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	_section_id = Column(BIGINT(10), ForeignKey('m_course_sections.id'), nullable=False, server_default=text("'0'"), name='section')
	_course_id = Column(BIGINT(10), ForeignKey('m_course.id'), name="course")

	completions = relationship("MCourseModulesCompletion", backref="coursemodule")

	def is_completed(self, user: MUser):
		session = Session.object_session(self)
		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user.id, MCourseModulesCompletion._coursemoduleid==self.id).all()
		completions = list(filter(lambda completion: completion.completed, completions)) # only keep completed courses
		return len(completions) > 0

	def __repr__(self) -> str:
		return f"Course module {self.id}"


class MCourseSection(Base):
	# parent course: MCourseModule.course	
	__tablename__ = 'm_course_sections'

	id = Column(BIGINT(10), primary_key=True)
	name = Column(String(255, 'utf8mb4_bin'))
	summary = Column(LONGTEXT)
	summaryformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
	sequence = Column(Sequence) # List containing MCourseModule id's in the order they should be traversed
	availability = Column(LONGTEXT)
	timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	_course_id = Column(BIGINT(10), ForeignKey('m_course.id'), name='course')
	_section_id = Column(BIGINT(10), nullable=False, server_default=text("'0'"), name='section')

	modules = relationship("MCourseModule", backref="section")

	def get_next_module(self, currentModule: MCourseModule):
		"""
		Returns: 
			MCourseModule (in order) that can be taken  after `currentModule`.
			Will return `None`, if no next module is defined for this section after `currentModule`.
		"""
		for index, moduleId in enumerate(self.sequence):
			if int(moduleId) == currentModule.id:
				# found position (index) of current module in order list - return following candidate
				if len(self.sequence) > index + 1:
					nextModuleId = int(self.sequence[index+1])
					return next(filter(lambda candidate: candidate.id == nextModuleId, self.modules), None)
		return None

	def __repr__(self) -> str:
		return f"Course section {self.name} ({self.id}): {self.summary}"



class MCourse(Base):
	__tablename__ = 'm_course'

	id = Column(BIGINT(10), primary_key=True)
	fullname = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))

	startdate = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	enddate = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	modules = relationship("MCourseModule", backref="course")
	sections = relationship("MCourseSection", backref='course')
	gradeItems = relationship("MGradeItem", backref='course')

	def __repr__(self) -> str:
		return f"Course {self.shortname} ({self.id}): Last modified: {self.timemodified}"
	

class UserInfo:
	def __init__(self, userid: int):
		self.userid = userid

	
engine, conn = connect_to_moodle_db()
Session = sessionmaker()
Session.configure(bind=engine)
Base.metadata.create_all(engine)