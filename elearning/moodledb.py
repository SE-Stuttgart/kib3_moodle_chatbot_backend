# coding: utf-8
import json
from typing import List, Tuple, Union
from sqlalchemy import Column, DECIMAL, String, text, create_engine, select, func
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT, TINYINT
from sqlalchemy.dialects.mysql.types import MEDIUMINT
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import SMALLINT
from sqlalchemy.types import TypeDecorator, Float, BOOLEAN
from urllib.parse import quote_plus as urlquote

from config import MOODLE_SERVER_ADDR, MOODLE_SERVER_DB_ADDR, MOODLE_SERVER_DB_PORT, MOODLE_SERVER_DB_TALBE_PREFIX, MOODLE_SERVER_DB_NAME, MOODLE_SERVER_DB_PWD, MOODLE_SERVER_DB_USER

Base = declarative_base()
metadata = Base.metadata

"""
These are some helper classes for interfacing with moodle DB datatypes.
They are not relevant for your application.
"""
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
"""
END Helper classes
"""

def connect_to_moodle_db(host=MOODLE_SERVER_DB_ADDR, port=MOODLE_SERVER_DB_PORT, user=MOODLE_SERVER_DB_USER, pwd=MOODLE_SERVER_DB_PWD, dbname=MOODLE_SERVER_DB_NAME):
	# NOTE: isolation level is important because moodle doesn't seem to commit to DB -> session data will be stale
	print("connecting...")
	# print(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4")
	engine = create_engine(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4", echo=False, future=True, isolation_level="READ UNCOMMITTED", pool_pre_ping=True, pool_recycle=3600, pool_reset_on_return=None)
	conn = engine.connect()
	print("done")
	return engine, conn



class MFile(Base):
	""" Access referenced files on server.
		WARNING: This function might not work on all possible moodle server configurations, 
				 thus we have to wait for a plugin from Kasra's students to search file contents from the php side instead the python side.
	""" 
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}files'

	id = Column(BIGINT(10), primary_key=True)
	contenthash = Column(String(40, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
	pathnamehash = Column(String(40, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''")) 

	# contextid = Column(BIGINT(10), nullable=False, index=True)
	filearea = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''")) # 'content', 'draft'

	filepath = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''")) # /
	filename = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''")) # e.g. 'Regression.pdf'
	source = Column(LONGTEXT) # source file name, e.g. 'Regression.pdf'

	mimetype = Column(String(100, 'utf8mb4_bin')) # e.g. "application/pdf"

	timecreated = Column(UnixTimestamp, nullable=False)
	timemodified = Column(UnixTimestamp, nullable=False)

	def get_server_file_path(self):
		""" real location of file on server: first three pairs of content hash are the path, filename = contenthash e.g. "b0ca8dasd....." -> "b0/ca/8d/b0ca8dasd....."  """
		return f"resources/moodledata/filedir/{self.contenthash[0:2]}/{self.contenthash[2:4]}/{self.contenthash}"



class MBookChapter(Base):
	"""
	Access parent Book via MBookChapter.book
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}book_chapters'

	id = Column(BIGINT(10), primary_key=True)

	pagenum = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
	subchapter = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	title = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	content = Column(LONGTEXT, nullable=False)
	contentformat = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	hidden = Column(TINYINT(2), nullable=False, server_default=text("'0'"))

	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	importsrc = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	
	_bookid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}book.id"), nullable=False, index=True, name="bookid")

	def get_parent_book(self):
		return self.book

class MBook(Base):
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}book'

	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
	
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro = Column(LONGTEXT)
	introformat = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	numbering = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	navstyle = Column(SMALLINT(), nullable=False, server_default=text("'1'"))
	customtitles = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
	revision = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	chapters: List[MBookChapter] = relationship("MBookChapter", backref="book")


class MGradeItem(Base):
	"""
	Definition of a gradable item, e.g. a quiz, containing
		* itemname, e.g. `Wo ist der Punkt im Koordinatensystem`
		* [grademin, grademax]: Interaval of possible grades students can obtain for this gradable item, e.g. in [0, 100] points

	Access related course via MGradeItem.course
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}grade_items'

	id = Column(BIGINT(10), primary_key=True)

	# name of the grade item, e.g. the specific quiz
	itemname = Column(String(255, 'utf8mb4_bin'))

	# less important info, tells if the GradeItem is from a HVP quiz, moodle quiz or other
	itemtype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	itemmodule = Column(String(30, 'utf8mb4_bin'))
	iteminstance = Column(BIGINT(10), nullable=False, server_default=text("'100'")) # link to course module

	# bounds of the grades possible for this grade
	grademax = Column(BIGINT(10), nullable=False, server_default=text("'100'"))
	gradepass = Column(BIGINT(10), nullable=False, server_default=("'0'"))
	grademin = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	# information about when gradeitem was created or updated by teacher
	timecreated = Column(UnixTimestamp)
	timemodified = Column(UnixTimestamp)

	# internal databasae table mapping information
	_courseid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), index=True, name='courseid')

	def get_parent_course(self):
		return self.course

	def __repr__(self) -> str:
		return f"""Grade Item: {self.itemname}"""


class MGradeGradesHistory(Base):
	""" Lists all previous and current grades per user and course """
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}grade_grades_history'

	id = Column(BIGINT(10), primary_key=True)
	oldid = Column(BIGINT(10), nullable=False, index=True) # old or current MGradeGrade.id 

	# timemodified tells when the current grade in the history was obtained
	timemodified = Column(UnixTimestamp, index=True)

	# grade info: rawgrade is in [rawgrademin, rawgrademax]
	# should be sufficient to use finalgrade instead
	rawgrade = Column(DECIMAL(10, 5))
	rawgrademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
	rawgrademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))

	# appropriately scaled rawgrade
	finalgrade = Column(DECIMAL(10, 5)) 

	# internal table mapping information
	_gradeItemId = Column(BIGINT(10), name="itemid") #, ForeignKey("MGradeItem.id"), nullable=False, index=True, name="itemid")
	_userid = Column(BIGINT(10), name="userid") # ForeignKey("MUser.id"), nullable=False, index=True, name="userid")

	def get_grade_item(self, session: Session) -> Union[MGradeItem, None]:
		""" Returns the MGradeItem associated with the current Grade object """
		try:
			# NOTE: Diese Tabelle enthält wahrscheinlich nicht was du suchst - in MGradeGrade stehen die aktuellen Noten,
			# das sollte deinem Einsatz entsprechen.
			# Ältere items in MGradeGrades History werden hier oft NONE zurück geben, weil der Link nicht mehr aktuell ist.
			return session.query(MGradeItem).get(self.oldid)
		except NoResultFound:
			return None

	def get_user(self, session: Session) -> "MUser":
		""" Returns the MUser object associated with the current Grade objet """
		return session.query(MUser).get(self._userid)

class MGradeGrade(Base):
	""" Current grade for a user in a course """
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}grade_grades'

	id = Column(BIGINT(10), primary_key=True)

	# grade info: rawgrade is in [rawgrademin, rawgrademax]
	# should be sufficient to use finalgrade instead
	rawgrade = Column(DECIMAL(10, 5))
	rawgrademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
	rawgrademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))

	# appropriately scaled rawgrade
	finalgrade = Column(DECIMAL(10, 5))

	# internal table mapping information
	_userid = Column(BIGINT(10), primary_key=True, name="userid") # Column(BIGINT(10), ForeignKey("MUser.id"), nullable=False, index=True)
	_gradeItemId = Column(BIGINT(10), primary_key=True, name="itemid") #Column(BIGINT(10), ForeignKey("MGradeItem.id"), nullable=False, index=True)
	
	def get_grade_item(self, session: Session) -> MGradeItem:
		#session.expire_all()
		return session.query(MGradeItem).get(self._gradeItemId)

	def get_user(self, session: Session) -> "MUser":
		return session.query(MUser).get(self._userid)


class MUserLastacces(Base):
	"""
	Log for user's last access, containing info about
		* which course was last accessed
		* and when
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}user_lastaccess'

	id = Column(BIGINT(10), primary_key=True)

	# last course access date
	timeaccess = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	# last accessed course object
	course = relationship("MCourse", back_populates="", uselist=False)

	user = relationship("MUser", back_populates="last_accessed_course", uselist=False) # user object

	# internal database mapping info
	_courseid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), nullable=False, index=True, server_default=text("'0'"), name='courseid')
	_userid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}user.id'), nullable=False, index=True, server_default=text("'0'"), name='userid')

	def __repr__(self) -> str:
		""" Pretty printing """
		return f"Last Access from user {self._userid} to Course {self._courseid} on {self.timeaccess}"




class MResource(Base):
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}resource'

	# TODO link relationships
	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro = Column(LONGTEXT)
	introformat = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	display = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))



class MModule(Base):
	""" Internal moodle content type mapping: Lookup e.g. for a MCourseModule what type it is """
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}modules'

	id = Column(BIGINT(10), primary_key=True)
	name = Column(String(20, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))


class MCourseModulesCompletion(Base):
	"""
	Information about what MCourseModule was finished when by what user.

	Access to parent coursemodule: MCourseModulesCompletion.coursemodule
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules_completion'

	id = Column(BIGINT(10), primary_key=True)

	# True if completed, else False
	completed = Column(CompletionState, nullable=False, name='completionstate')
	# Date of completion
	timemodified = Column(UnixTimestamp, nullable=False)
	#viewed = Column(SMALLINT(), nullable=True, server_default=text("'0'"))

	# internal database mapping info
	_coursemoduleid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules.id"), nullable=False, index=True, name="coursemoduleid")
	_userid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}user.id"), nullable=False, name="userid") # TODO relation to user

	def __repr__(self) -> str:
		""" Pretty printing """
		return f"Completion: course_module_id {self._coursemoduleid}: {self.completed} for user {self._userid}"


class MCourseModulesViewed(Base):
	"""
	Information about what MCourseModule was viewed when by what user.
	Access to parent coursemodule: MCourseModulesViewed.coursemodule
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules_viewed'

	id = Column(BIGINT(10), primary_key=True)

	# Date of viewing
	timecreated = Column(UnixTimestamp, nullable=False)

	# internal database mapping info
	_coursemoduleid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules.id"), nullable=False, index=True, name="coursemoduleid")
	_userid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}user.id"), nullable=False, name="userid") # TODO relation to user

	def __repr__(self) -> str:
		""" Pretty printing """
		return f"Completion: course_module_id {self._coursemoduleid} for user {self._userid}"



class MHVP(Base):
	# TODO finish
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}hvp'

	# TODO link relationships
	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro = Column(LONGTEXT)
	introformat = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

class MCourseModule(Base):
	"""
	Definition of a course module.
	Includes information about
		* date the course module was added to moodle
		* a list with completion status per user

	Access parent course: MCourseModule.course
	Access parent section: MCourseModule.section
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules'

	id = Column(BIGINT(10), primary_key=True)
	added = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	availability = Column(LONGTEXT) # input for is_available method (json_condition)

	completions = relationship("MCourseModulesCompletion", backref="coursemodule")
	views = relationship("MCourseModulesViewed", backref="coursemodule")

	# internal database mapping info
	_section_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_sections.id'), nullable=False, server_default=text("'0'"), name='section')
	_course_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), name="course")
	_type_id = Column(String(255, 'utf8mb4_bin'), name='module') # type of content, e.g. resource, book, ...
	instance = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	visible = Column(SMALLINT(), nullable=False, server_default=text("'1'"))

	def get_content_link(self, session: Session):
		# TODO Dirk: ist es richtig, dass das erste Element genommen werden muss? Wenn ich nach dem content eines Moduls (Section)frage, wird mir den Link zu dem assignement vorgeschlagen
		# Falsche Links bekommen
		#session.expire_all()
		base_path = f"http://{MOODLE_SERVER_ADDR()}"
		type_info = self.get_type_name(session)
		if type_info == "book":
			return f'<a href="{base_path}/mod/book/view.php?id={self.id}">{self.get_name(session)}</a>' # &chapter={}
			# TODO later add chapters (for search), correlate page number in m_book_chapter
		elif type_info == "assign":
			return f'<a href="{base_path}/mod/assign/view.php?id={self.id}">{self.get_name(session)}</a>'
		elif type_info == 'resource':
			return f'<a href="{base_path}/mod/resource/view.php?id={self.id}">{self.get_name(session)}</a>'
		elif type_info == "glossary":
			return f'<a href="{base_path}/mod/glossary/view.php?id={self.id}">{self.get_name(session)}</a>'
		elif type_info == "hvp":
			return f'<a href="{base_path}/mod/hvp/view.php?id={self.id}">{self.get_name(session)}</a>'
		else: 
			return f'<a href="{base_path}/mod/{type_info}/view.php?id={self.id}">{self.get_name(session)}</a>'

	def get_hvp_embed_html(self, session: Session) -> Union[str, None]:
		""" Returns the <iframe/> code to embed the h5p content if this course module is h5p content, else None """
		#session.expire_all()
		type_info = self.get_type_name(session)
		# print("TYPE INFO", type_info)
		if type_info == "hvp":
			return f"""
			<iframe src="http://{MOODLE_SERVER_ADDR()}/mod/hvp/embed.php?id={self.id}" allowfullscreen="allowfullscreen"
				title="Multiple Choice: Welche Zusammenhänge sind kausal?" width="350" height="350" frameborder="0"></iframe>
			<script src="../../mod/hvp/library/js/h5p-resizer.js" charset="UTF-8"></script>
			"""
		return None # Not h5p content

	def is_completed(self, user: "MUser", session: Session) -> bool:
		""" Query if user has completed this course module.

		Args:
			user (MUser): the user to check completion for this course module

		Returns:
			completion state (bool): True, if user completed this course module, else False
		"""
		#session.expire_all()
		return session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user.id, MCourseModulesCompletion._coursemoduleid==self.id, MCourseModulesCompletion.completed==True).count() > 0

	def get_name(self, session: Session):
		#session.expire_all()
		type_info = self.get_type_name(session)
		if type_info == "book":
			return session.query(MBook).get(self.instance).name
		elif type_info == "assign":
			return session.query(MAssign).get(self.instance).name
		elif type_info == 'resource':
			return session.query(MResource).get(self.instance).name
		elif type_info == "glossary":
			return "Glossar"
		elif type_info == "hvp":
			return session.query(MHVP).get(self.instance).name
		elif type_info == "page":
			# Section hat ein Attribut name, dass modul selbst nicht
			return self.section.name
		else: 
			return None
	
	def get_type_name(self, session: Session):
		#session.expire_all()
		return session.query(MModule).get(self._type_id).name

	def __repr__(self) -> str:
		""" Pretty printing """
		return f"Course module {self.id}, type {self._type_id}"




class MCourseSection(Base):
	"""
	Definition of a course section, including
		* name
		* summary
		* sequence/order in which MCourseModules should be traversed
		* time last modified by a teacher
		* list of modules belonging to this course section
	"""
	# parent course: MCourseModule.course
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_sections'

	id = Column(BIGINT(10), primary_key=True)

	# general course info
	name = Column(String(255, 'utf8mb4_bin'))
	summary = Column(LONGTEXT)
	summaryformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
	availability = Column(LONGTEXT) # input for is_available (json_condition)
	visible = Column(SMALLINT(), nullable=False, server_default=text("'1'"))

	# List containing MCourseModule id's in the order they should be traversed by students
	sequence = Column(Sequence)
	# Last modification date by teacher
	timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	# list of associated modules
	modules = relationship("MCourseModule", backref="section")

	# internal database mapping info
	_course_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), name='course')
	_section_id = Column(BIGINT(10), nullable=False, server_default=text("'0'"), name='section')


	def get_next_available_module(self, currentModule: MCourseModule, user: "MUser", session: Session, included_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> Union[MCourseModule, None]:
		"""
		Given a current course module (e.g. the most recently finished one) in this course section,
		find the course module the student should do next.

		Args:
			currentModule: if None, will return first available module in section
			included_types: obtain e.g. via MCourseModule.get_type_name()
							PDF = resource

		Returns: 
			MCourseModule (in order) that can be taken  after `currentModule`.
			Will return `None`, if no next module is defined for this section after `currentModule`.
		"""
		#session.expire_all()
		# print("SEQUENCE", self.sequence, 'name', self.name, 'id', self.id)

		for index, moduleId in enumerate(self.sequence):
			if not currentModule:
				nextModuleId = int(self.sequence[index])
				module = session.query(MCourseModule).get(nextModuleId)
				if is_available_course_module(session, user, module) and module.get_type_name(session) in included_types:
					return next(filter(lambda candidate: candidate.id == nextModuleId, self.modules), None)
			elif int(moduleId) == currentModule.id:
				# found position (index) of current module in order list - return following candidate
				if len(self.sequence) > index + 1:
					nextModuleId = int(self.sequence[index+1])
					module = session.query(MCourseModule).get(nextModuleId)
					if is_available_course_module(session, user, module) and module.get_type_name(session) in included_types:
						return next(filter(lambda candidate: candidate.id == nextModuleId, self.modules), None)
		return None
	
	def get_link(self):
		""" Get link to course section """
		return f"http://{MOODLE_SERVER_ADDR()}/course/view.php?id={self._course_id}&section={self._section_id}"

	def is_completed(self, user: "MUser", session: Session) -> bool:
		""" Query if user has completed this course section (= all course modules inside this course section).
			Users have to mark all activities inside this section as done manually.

		Args:
			user (MUser): the user to check completion for this course section

		Returns:
			completion state (bool): True, if user completed this course section, else False
		"""
		#session.expire_all()
		page_id = session.query(MModule).filter(MModule.name=="page").all() #with_entities(text("id"))
		
		all_section_module_ids = set([course_module.id for course_module in session.query(MCourseModule).filter(MCourseModule._section_id==self.id, MCourseModule._type_id!=page_id[0].id).all()])
		
		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user.id).all()
		completed_section_modules = [completion._coursemoduleid for completion in completions if completion._coursemoduleid in all_section_module_ids]
		return len(all_section_module_ids.difference(completed_section_modules)) == 0

	def __repr__(self) -> str:
		return f"Course section {self.name} ({self.id})"


class MCourse(Base):
	"""
	Definition of a moodle course.
	Includes information about
		* name
		* begin / end dates
		* creation / last modified dates by teacher
		* list of course modules belonging to this course
		* list of sections in this course
		* list of gradable items in this course, e.g. quizzes
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}course'

	# general course info
	id = Column(BIGINT(10), primary_key=True)
	fullname = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))

	# being / end date for students
	startdate = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	enddate = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	# creation / last modified dates by teachers
	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	# associated materials
	modules = relationship("MCourseModule", backref="course")
	sections = relationship("MCourseSection", backref='course')
	gradeItems = relationship("MGradeItem", backref='course')

	def __repr__(self) -> str:
		""" Pretty printing """
		return f"Course {self.shortname} ({self.id}): Last modified: {self.timemodified}"


class MAssignGrade(Base):
	"""
	Access MAssign via MAssignGrade.assign
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}assign_grades'

	id = Column(BIGINT(10), primary_key=True)
	
	_assign_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}assign.id'), nullable=False, index=True, name="assign")
	userid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}user.id"), nullable=False, index=True)

	timecreated = Column(UnixTimestamp, nullable=True)
	timemodified = Column(UnixTimestamp, nullable=True)

	grade = Column(DECIMAL(10, 5), server_default=text("'0.00000'"))
	attemptnumber = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MAssign(Base):
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}assign'

	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro = Column(LONGTEXT, nullable=False)
	nosubmissions = Column(TINYINT(2), nullable=False, server_default=text("'0'"))

	duedate = Column(UnixTimestamp, nullable=True)
	cutoffdate = Column(UnixTimestamp, nullable=True)
	
	allowsubmissionsfromdate = Column(UnixTimestamp, nullable=True)
	timemodified = Column(UnixTimestamp, nullable=True)

	maxattempts = Column(MEDIUMINT(6), nullable=False, server_default=text("'-1'"))

	grades = relationship("MAssignGrade", backref="assign")
	submissions = relationship("MAssignSubmission", backref="assign")


class MAssignSubmission(Base):
	""" Access related assign via MAssignSubmission.assign """
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}assign_submission'

	id = Column(BIGINT(10), primary_key=True)

	_assign_id = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}assign.id"), nullable=False, index=True, name='assignment')
	_user_id = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}user.id"), nullable=False, index=True, name="userid")

	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	status = Column(String(10, 'utf8mb4_bin')) # either new or submitted
	
	attemptnumber = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	latest = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MChatbotWeeklySummary(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}chatbot_weekly_summary"

	_userid = Column(BIGINT(10), primary_key=True, name="userid") # Column(BIGINT(10), ForeignKey("MUser.id"), nullable=False, index=True)
	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	firstweek = Column(BOOLEAN, nullable=False)

class MChatbotProgressSummary(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}chatbot_progress_summary"

	_userid = Column(BIGINT(10), primary_key=True, name="userid") # Column(BIGINT(10), ForeignKey("MUser.id"), nullable=False, index=True)
	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	progress = Column(Float, nullable=False)

class MTag(Base):
	""" Inside the tags, we store information like estimated duration of a course module """
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}tag'

	id = Column(BIGINT(10), primary_key=True)

	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	rawname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	
	timemodified = Column(UnixTimestamp)
	instances = relationship('MTagInstance', backref='tag')


class MTagInstance(Base):
	""" Access tag via MTagInstance.tag """
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}tag_instance'

	id = Column(BIGINT(10), primary_key=True)

	itemtype = Column(String(100, 'utf8mb4_bin'), nullable=False) # e.g. course_modules
	itemid = Column(BIGINT(10), nullable=False)	

	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	_tagid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}tag.id"), nullable=False, index=True, name='tagid')



class MUser(Base):
	"""
	A moodle user, containing
		* username
		* last login date
		* last accessed course
		* grades
			* grade history
		* list of completed courses
		* last completed course module
	"""
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}user'

	# user information
	id = Column(BIGINT(10), primary_key=True)
	username = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	idnumber = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
	firstname = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
	middlename = Column(String(255, 'utf8mb4_bin'), index=True)
	lastname = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
	alternatename = Column(String(255, 'utf8mb4_bin'), index=True)

	# last login date, user data modification dates, ...
	lastlogin = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	currentlogin = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	firstaccess = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	lastaccess = Column(UnixTimestamp, nullable=False, index=True, server_default=text("'0'"))
	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	# last accessed course
	last_accessed_course = relationship("MUserLastacces", back_populates="user", uselist=False)

	def get_grades(self, session: Session, course_id: int) -> List[MGradeGrade]:
		""" Return all current grades of the current user (for the specified course) """
		#session.expire_all()
		course_grade_items = session.query(MGradeItem).filter(MGradeItem._courseid==course_id).all()
		results = []
		for grade_item in course_grade_items:
			results += session.query(MGradeGrade).filter(MGradeGrade._gradeItemId==grade_item.id, MGradeGrade._userid==self.id, MGradeGrade.finalgrade != None).all()
		return results
	
	def count_grades(self, session: Session, course_id: int) -> int:
		""" Return the number of quizzes a user has completed (at least once) """
		#session.expire_all()
		course_grade_items = session.query(MGradeItem).filter(MGradeItem._courseid==course_id).all()
		results = 0
		for grade_item in course_grade_items:
			results += session.query(MGradeGrade).filter(MGradeGrade._gradeItemId==grade_item.id, MGradeGrade._userid==self.id, MGradeGrade.finalgrade != None).count()
		return results

	def count_repeated_grades(self, session: Session, course_id: int) -> int:
		""" Return the number of quizzes a user has repeated at least once """
		#session.expire_all()
		course_grade_items = session.query(MGradeItem).filter(MGradeItem._courseid==course_id).all()
		results = 0
		for grade_item in course_grade_items:
			results += session.query(MGradeGradesHistory).filter(MGradeGradesHistory._gradeItemId==grade_item.id, MGradeGradesHistory._userid==self.id, MGradeGradesHistory.finalgrade != None).count() >= 2
		return results

	def get_grade_history(self, session: Session) -> List[MGradeGradesHistory]:
		""" Return all current and past grades of the current user (for all courses) """
		#session.expire_all()
		return session.query(MGradeGradesHistory).filter(MGradeGradesHistory._userid==self.id).all()

	def get_all_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> List[MCourseModule]:
		""" Return all course modules already completed by current user in the specified course """
		#session.expire_all()
		coursemodules = session.query(MCourseModule).filter(MCourseModule._course_id==courseid)
		return [coursemodule for coursemodule in coursemodules if coursemodule.get_type_name(session) in include_types]

	def get_completed_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz'], timerange: List[int] = None) -> List[MCourseModulesCompletion]:
		""" Return all course modules already completed by current user in the specified course """
		#session.expire_all()
		
		if not isinstance(timerange, type(None)):
			start_time = timerange[0]
			end_time = timerange[1]
			completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True) \
																		.filter(MCourseModulesCompletion.timemodified >= start_time) \
																		.filter(MCourseModulesCompletion.timemodified <= end_time)
			return [completion.coursemodule for completion in completions if completion.coursemodule.get_type_name(session) in include_types and completion.coursemodule._course_id==courseid]	
		else:
			completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True)
			return [completion.coursemodule for completion in completions if completion.coursemodule.get_type_name(session) in include_types and completion.coursemodule._course_id==courseid]

	def get_viewed_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz'], timerange: List[int] = None) -> List[MCourseModulesCompletion]:
		""" Return all course modules already completed by current user in the specified course """
		#session.expire_all()
		
		if not isinstance(timerange, type(None)):
			start_time = timerange[0]
			end_time = timerange[1]
			views = session.query(MCourseModulesViewed).filter(MCourseModulesViewed._userid==self.id) \
																		.filter(MCourseModulesViewed.timecreated >= start_time) \
																		.filter(MCourseModulesViewed.timecreated <= end_time)
			return [view.coursemodule for view in views if view.coursemodule.get_type_name(session) in include_types and view.coursemodule._course_id==courseid]	
		else:
			views = session.query(MCourseModulesViewed).filter(MCourseModulesViewed._userid==self.id)
			return [view.coursemodule for view in views if view.coursemodule.get_type_name(session) in include_types and view.coursemodule._course_id==courseid]


	def is_completed(self, session: Session, module_id: int ,courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> bool:
		""" Return wheteher a module  is completed by this user or not """
		#session.expire_all()
		completions = self.get_completed_course_modules(session, courseid, include_types)
		for completion in completions:
			if module_id == completion.id:
				return True
		return False

	def get_completed_course_modules_before_date(self, date, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> List[MCourseModulesCompletion]:
		""" Return all course modules already completed by current user before a date """
		#session.expire_all()
		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True)
		return [completion.coursemodule for completion in completions if completion.coursemodule.get_type_name(session) in include_types and completion.coursemodule._course_id==courseid]

	def get_not_finished_courses_before_date(self, date, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> List[MCourseModulesCompletion]:
		""" Return all course modules already completed by current user """
		#session.expire_all()
		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==False, MCourseModulesCompletion.timemodified < date)
		return [completion.coursemodule for completion in completions if completion.coursemodule.get_type_name(session) in include_types and completion.coursemodule._course_id==courseid]

	def find_quiz_by_course_id(self, course_id, session: Session):
		"""
			Returns next quiz for Module with name equals module_name
		"""
		#session.expire_all()
		# TODO test
		# Tested: it searches for section and not for module_name
		quiz_types = session.query(MModule).filter((MModule.name=="hvp")).all() # TODO re-enable at some point? | (MModule.name=="quiz")).all()
		quizes = []
		for quiz_type in quiz_types:
			# Fixme es funktioniert nicht gut, es findet mehr als erwartet
			quizes += session.query(MCourseModule).filter((MCourseModule._course_id==course_id) & (MCourseModule._type_id==quiz_type.id)).all()
		return quizes

	def find_quiz_by_course_module_id(self, course_module_id, session: Session):
		"""
			Returns next quiz for Module with name equals module_name
		"""
		#session.expire_all()
		# TODO test
		# Tested: it searches for section and not for module_name
		quiz_types = session.query(MModule).filter((MModule.name=="hvp")).all() # TODO re-enable at some point? | (MModule.name=="quiz")).all()
		quizes = []
		for quiz_type in quiz_types:
			# Fixme es funktioniert nicht gut, es findet mehr als erwartet
			quizes += session.query(MCourseModule).filter((MCourseModule.id==course_module_id) & (MCourseModule._type_id==quiz_type.id)).all()
		return quizes
		
	def get_enrolled_course(self) -> List[MCourseModule]:
		"""
			Return all courses user is enrolled in
		"""
		# Diese Funktion ist fuer unser Szenario nicht wichtig, da es eigentlich nur einen einzigen Kurs gibt, und alle Teilnehmer fuer diesen eingeschrieben werden
		raise NotImplementedError

	# Fixme? return type(Union[MCourseModule, None]) is different from what the function returns in reality (Union[MCourseModulesCompletion, None])
	# -> sollte eigentlich stimmen, beim return wird .coursemodule vom MCourseModulesCompletion zurueckgegeben
	def get_last_completed_coursemodule(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> Union[MCourseModule, None]:
		""" Get the course module the current user completed most recently.
			If there is no completed module yet, return the first one
		Returns:
			* last completed course module (MCourseModule), if the user already completed any course module, else `None`
		"""
		#session.expire_all()
		completions: List[MCourseModulesCompletion] = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True).all()
		
		completions = list(filter(lambda comp: comp.coursemodule.get_type_name(session) in include_types and comp.coursemodule._course_id==courseid, completions))

		if len(completions) == 0:
			available_modules = self.get_available_course_modules(session, courseid=courseid)
			if len(available_modules) == 0:
				return available_modules[0] # return first result
			else:
				return None
		return max(completions, key=lambda comp: comp.timemodified).coursemodule

	def get_last_completed_quiz(self, session: Session, courseid: int) -> Union[MCourseModule, None]:
		""" Get the course module the current user completed most recently.
			If there is no completed module yet, return the first one
		Returns:
			* last completed course module (MCourseModule), if the user already completed any course module, else `None`
		"""
		#session.expire_all()
		completions: List[MHVP] = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True).all()
		completions = [completion for completion in completions if completion.coursemodule._course_id==courseid]
		if len(completions) == 0:
			return self.get_available_course_modules(session, courseid=courseid)[0] # return first result
		return max(completions, key=lambda comp: comp.timemodified).coursemodule

	def get_not_completed_courses(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> List[MCourseModule]:
		""" Return all course modules not completed by current user """
		#session.expire_all()
		completed = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True)
		completed_ids = [complete._coursemoduleid for complete in completed if complete.coursemodule.get_type_name(session) in include_types and complete.coursemodule._course_id==courseid]
		courses = session.query(MCourseModule).all()
		return [course for course in courses if course.id not in completed_ids]

	def get_available_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> List[MCourseModule]:
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if is_available_course_sections(session, self, section):
				for course_moudule in section.modules:
					if is_available_course_module(session, self, course_moudule) and course_moudule.get_type_name(session) in include_types:
						available.append(course_moudule)
		return available

	def get_available_course_sections(self, session: Session, courseid: int) -> List[MCourseSection]:
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if is_available_course_sections(session, self, section):
				available.append(section)
		return available

	def get_incomplete_available_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> List[MCourseModule]:
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if is_available_course_sections(session, self, section):
				for course_moudule in section.modules:
					if not course_moudule.is_completed(self, session) and is_available_course_module(session, self, course_moudule) and course_moudule.get_type_name(session) in include_types:
						available.append(course_moudule)
		return available		
	
	def get_incomplete_available_course_sections(self, session: Session, courseid: int) -> List[MCourseSection]:
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if (not section.is_completed(self, session) and is_available_course_sections(session, self, section) 
				and section.name and not section.name.lower().startswith("ki und maschinelles lernen") 
				and not section.name.lower().startswith("nicht-finale version")  and not section.name.lower().startswith("spiel zum einstieg")):
				available.append(section)
		return available

	def __repr__(self) -> str:
		""" Pretty printing """
		return f"""User {self.username} ({self.id})
			- Last login: {self.lastlogin}
			- Last accessed course: {self.last_accessed_course.course if self.last_accessed_course else None}
		"""
		# - Grades: {self.get_grades()}


def is_available(json_condition: str, session: Session, user: MUser, current_server_time: int) -> bool:
	#session.expire_all()
	if not json_condition:
		return True # no restrictions

	data = json.loads(json_condition)
	if not data['c']:
		return True # no restrictions

	# check conditions
	fullfilled = []
	for condition in data["c"]:
		if not "type" in condition:
			continue
		# TODO handle nested conditions:
		# {'op': '&', 'showc': [False, False, False, False, False], 'c': [{'type': 'grade', 'id': 4, 'min': 50}, {'type': 'grade', 'id': 3, 'min': 50}, {'type': 'grade', 'id': 5, 'min': 50}, {'type': 'grade', 'id': 2, 'min': 50}, {'op': '|', 'c': [{'type': 'grade', 'id': 2, 'max': 80}, {'type': 'grade', 'id': 4, 'max': 80}, {'type': 'grade', 'id': 3, 'max': 80}, {'type': 'grade', 'id': 5, 'max': 80}]}]}
		if condition['type'] == 'completion':
			course_module = session.query(MCourseModule).get(condition['cm'])
			if course_module:
				completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user.id, MCourseModulesCompletion._coursemoduleid==course_module.id).all()
				if completions:
					fullfilled.append(int(completions[0].completed) == condition['e'])
				else:
					fullfilled.append(condition['e']==0)
		elif condition['type'] == 'date':
			unixTime = datetime.datetime.utcfromtimestamp(condition['t'])
			if condition['d'] == ">=":
				fullfilled.append(current_server_time >= unixTime)
			elif condition['d'] == "<":
				fullfilled.append(current_server_time <= unixTime)
			else:
				assert False, "Unknown date comparison operator"
	if len(fullfilled) == 0:
		return True
	return any(fullfilled) if data['op']=="|" else all(fullfilled)


def is_available_course_module(session: Session, user: MUser, course_module: MCourseModule):
	#session.expire_all()
	return bool(course_module.visible) and is_available(json_condition=course_module.availability, session=session, user=user)


def is_available_course_sections(session: Session, user: MUser, section: MCourseSection):
	#session.expire_all()
	return bool(section.visible) and is_available(json_condition=section.availability, session=session, user=user)




def get_time_estimate_module(session: Session, user: MUser, course_module: MCourseModule) -> Union[int, None]:
	#session.expire_all()
	already_completed = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user.id)
	if is_available_course_module(session, user, course_module) and already_completed.filter(MCourseModulesCompletion._coursemoduleid==course_module.id).count() == 0:
		# course module is available and has not already been completed
		# -> find time tag if available
		module_tag_instances = session.query(MTagInstance).filter(MTagInstance.itemtype=='course_modules', MTagInstance.itemid==course_module.id).all()
		time_estimate = None
		for tag_instance in module_tag_instances:
			if tag_instance.tag.name.strip().startswith('dauer:'):
				# found time estimate tag
				time_estimate = tag_instance.tag.name.strip().split(":")[1] # xy minuten/min/mins
				assert "min" in time_estimate, "Unkown time type in time estimate"
				if "min" in time_estimate:
					minute_estimate = int(time_estimate.replace("minuten", "").replace("mins", "").replace("min", "").strip())
					return minute_estimate
	return None

def get_time_estimates(session: Session, user: MUser, courseid: int, include_types: List[str] = ['assign', 'book', 'hvp', 'page', 'quiz']) -> List[Tuple[MCourseModule, int]]:
	""" 
	Returns:
		a list of tuples: 
			* Each entry in list is a combination of a course module and its estimated completion time (in minutes)
	"""
	#session.expire_all()
	course_modules = session.query(MCourseModule).filter(MCourseModule._course_id==courseid)
	course_modules = filter(lambda module: module.get_type_name(session) in include_types, course_modules)
	estimates = []
	for module in course_modules:
		mod_estimate = get_time_estimate_module(session, user, module)
		if mod_estimate:
			estimates.append((module, mod_estimate))
	return estimates
		

def get_time_estimate_section(session: Session, user: MUser, section: MCourseSection) -> int:
	#session.expire_all()
	estimate = 0
	for course_module in section.modules:
		mod_estimate = get_time_estimate_module(session, user, course_module)
		if mod_estimate:
			estimate += mod_estimate
	return estimate


# def example():
# 	""" An example of how to connect to the database and extract the information """

# 	# connect to database
# 	engine, conn = connect_to_moodle_db()
# 	Session = sessionmaker()
# 	Session.configure(bind=engine)
# 	Base.metadata.create_all(engine)

# 	with Session() as session:
# 		# get last user from user database table
# 		muser: MUser = session.query(MUser).all()[-1]
# 		print(muser)
# 		# print("\n\n")

# 		# # get info about courses
# 		# print("FOUND COURSES:")
# 		# for course in session.query(MCourse).all():
# 		# 	print(course)
# 		# 	# for module in course.modules:
# 		# 	# 	print(" - module: ", module)
# 		# 	# 	print("   -", module.section)
# 		# 	#		print("  (in section)", module.section.name)
# 		# 	for section in course.sections:
# 		# 		print(" - ", section)
# 		# 		print("      (order: ", section.sequence, ")")
# 		# 		for module in section.modules:
# 		# 			print("    - ", module)
# 		# 			print("     COMPLETED:", module.is_completed(muser))
# 		# 			print("     ==>  next module: ", section.get_next_module(module))

# 		print("TIME ESTIMATES")
# 		print(get_time_estimates(session, muser))
# 		print("AVAILABLE COURSE MODULES")
# 		for mod in muser.get_incomplete_available_course_modules():
# 			print(" - ", mod.id, mod._type_id, mod.section)
# 		print("AVAILABLE COURSE SECTIONS")
# 		for sec in muser.get_incomplete_available_course_sections():
# 			print(" - ", sec.name)


# 	conn.close()

# if __name__ == "__main__":
# 	example()
