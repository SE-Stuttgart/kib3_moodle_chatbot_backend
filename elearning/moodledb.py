# coding: utf-8
import json
import re
from enum import Enum
import random
from typing import List, Tuple, Union
from sqlalchemy import Column, DECIMAL, String, text, create_engine, desc, Text
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
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

from config import MOODLE_SERVER_DB_ADDR, MOODLE_SERVER_DB_PORT, MOODLE_SERVER_DB_TALBE_PREFIX, MOODLE_SERVER_DB_NAME, MOODLE_SERVER_DB_PWD, MOODLE_SERVER_DB_USER, MOODLE_SERVER_URL

class Base:
    __allow_unmapped__ = True


Base = declarative_base(cls=Base)
# Base = declarative_base()
metadata = Base.metadata


"""
Regexes
"""
re_topic_branch = re.compile(r'Thema ([A-Z])\d(-\d+)?:')

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
	impl = Text

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
	

class BadgeMethodEnum(Enum):
	AGGREGATION_ALL = 1
	AGGREGATION_ANY = 2

class BadgeMethod(TypeDecorator):
	impl = TINYINT

	def process_bind_param(self, value, dialect):
		return value.value

	def process_result_value(self, value, dialect):
		return BadgeMethodEnum(value)



class BadgeCompletionStatus(Enum):
	INCOMPLETE = 0
	COMPLETED = 1
	CLAIMED = 2	


class BadgeStatusEnum(Enum):
	INACTIVE = 0
	ACTIVE = 1
	INACTIVE_LOCKED = 2
	ACTIVE_LOCKED = 3
	ARCHIVED = 4

class BadgeStatus(TypeDecorator):
	impl = TINYINT

	def process_bind_param(self, value, dialect):
		return value.value

	def process_result_value(self, value, dialect):
		return BadgeStatusEnum(value)


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

	itemid = Column(BIGINT(10), primary_key=True)
	contextid = Column(BIGINT(10), nullable=False, index=True)
	filearea = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''")) # 'content', 'draft', "package"
	component = Column(Text) # module name

	filepath = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''")) # /
	filename = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''")) # e.g. 'Regression.pdf'
	source = Column(Text) # source file name, e.g. 'Regression.pdf'

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
	content = Column(Text, nullable=False)
	contentformat = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	hidden = Column(TINYINT(2), nullable=False, server_default=text("'0'"))

	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))

	importsrc = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	
	_bookid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}book.id"), nullable=False, index=True, name="bookid")

	def get_parent_book(self):
		return self.book
	
class MUrl(Base):
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}url'
	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))

	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	externalurl = Column(Text)


class MBook(Base):
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}book'

	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
	
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro = Column(Text)
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
	intro = Column(Text)
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


class MContext(Base):
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}context'
	id = Column(BIGINT(10), primary_key=True)
	
	course_module = relationship("MCourseModule", back_populates="context", uselist=False)

	_instanceid = Column(BIGINT(10), ForeignKey(f"{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules.id"), nullable=False, index=True, name="instanceid")


class MHVP(Base):
	# TODO finish
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}hvp'

	# TODO link relationships
	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro = Column(Text)
	introformat = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	timemodified = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))


class MH5PActivity(Base):
	# TODO finish
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}h5pactivity'

	# TODO link relationships
	id = Column(BIGINT(10), primary_key=True)
	course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro = Column(Text)
	introformat = Column(SMALLINT(), nullable=False, server_default=text("'0'"))
	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
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
	availability = Column(Text) # input for is_available method (json_condition)

	completions = relationship("MCourseModulesCompletion", backref="coursemodule")
	views = relationship("MCourseModulesViewed", backref="coursemodule")
	recently_accessed_items = relationship("MChatbotRecentlyAcessedItem", back_populates="coursemodule")
	context = relationship("MContext", back_populates="course_module", uselist=False)

	# internal database mapping info
	_section_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_sections.id'), nullable=False, server_default=text("'0'"), name='section')
	_course_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), name="course")
	_type_id = Column(String(255, 'utf8mb4_bin'), name='module') # type of content, e.g. resource, book, ...
	instance = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
	visible = Column(SMALLINT(), nullable=False, server_default=text("'1'"))
	
	def is_viewed(self):
		return len(self.views) > 0

	def get_content_link(self, session: Session, alternative_display_text: Union[None, str] = None):
		# TODO Dirk: ist es richtig, dass das erste Element genommen werden muss? Wenn ich nach dem content eines Moduls (Section)frage, wird mir den Link zu dem assignement vorgeschlagen
		# Falsche Links bekommen
		#session.expire_all()
		base_path = MOODLE_SERVER_URL
		type_info = self.get_type_name(session)
		display_name = self.get_name(session) if isinstance(alternative_display_text, type(None)) else alternative_display_text
		if type_info == "book":
			return f'<a href="{base_path}/mod/book/view.php?id={self.id}">{display_name}</a>' # &chapter={}
			# TODO later add chapters (for search), correlate page number in m_book_chapter
		elif type_info == "assign":
			return f'<a href="{base_path}/mod/assign/view.php?id={self.id}">{display_name}</a>'
		elif type_info == 'resource':
			return f'<a href="{base_path}/mod/resource/view.php?id={self.id}">{display_name}</a>'
		elif type_info == "glossary":
			return f'<a href="{base_path}/mod/glossary/view.php?id={self.id}">{display_name}</a>'
		elif type_info == "hvp":
			return f'<a href="{base_path}/mod/hvp/view.php?id={self.id}">{display_name}</a>'
		elif type_info == "url":
			return f'<a href="{base_path}/mod/url/view.php?id={self.id}">{display_name}</a>'
		else: 
			return f'<a href="{base_path}/mod/{type_info}/view.php?id={self.id}">{display_name}</a>'

	def get_h5p_parameters(self, session: Session):
		file = session.query(MFile).filter(MFile.contextid==self.context.id,MFile.filename.endswith(".h5p")).first()
		return {
			"host": MOODLE_SERVER_URL,
			"context": self.context.id,
			"filearea": file.filearea,
			"itemid": file.itemid,
			"filename": file.filename
		}

	def get_hvp_embed_html(self, session: Session) -> Union[str, None]:
		""" Returns the <iframe/> code to embed the h5p content if this course module is h5p content, else None """
		#session.expire_all()
		type_info = self.get_type_name(session)
		# print("TYPE INFO", type_info)
		if type_info == "hvp":
			return f"""
			<iframe src="{MOODLE_SERVER_URL}/mod/hvp/embed.php?id={self.id}" allowfullscreen="allowfullscreen"
				title="Multiple Choice: Welche Zusammenhänge sind kausal?" frameborder="0"></iframe>
			<script src="../../mod/hvp/library/js/h5p-resizer.js" charset="UTF-8"></script>
			"""
		elif type_info == "h5pactivity":
			file = session.query(MFile).filter(MFile.contextid==self.context.id,MFile.filename.endswith(".h5p")).first()
			return f"""<iframe src="{MOODLE_SERVER_URL}/h5p/embed.php?url={MOODLE_SERVER_URL}/pluginfile.php/{self.context.id}/mod_h5pactivity/{file.filearea}/{file.itemid}/{file.filename}&preventredirect=1&component=mod_h5pactivity" name="h5player" allowfullscreen="allowfullscreen" class="h5p-player border-0 block_chatbot-quiz"></iframe>
			<script src="{MOODLE_SERVER_URL}/h5p/h5plib/v124/joubel/core/js/h5p-resizer.js"></script>
			"""
		return None # Not h5p content

	def is_completed(self, user_id: int, session: Session) -> bool:
		""" Query if user has completed this course module.

		Args:
			user (MUser): the user to check completion for this course module

		Returns:odule,
			completion state (bool): True, if user completed this course m else False
		"""
		#session.expire_all()
		return session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user_id, MCourseModulesCompletion._coursemoduleid==self.id, MCourseModulesCompletion.completed==True).count() > 0

	def get_name(self, session: Session):
		#session.expire_all()
		type_info = self.get_type_name(session)
		if type_info == "book":
			return session.get(MBook, self.instance).name
		elif type_info == "assign":
			return session.get(MAssign, self.instance).name
		elif type_info == 'resource':
			return session.get(MResource, self.instance).name
		elif type_info == "glossary":
			return "Glossar"
		elif type_info == "hvp":
			return session.get(MHVP, self.instance).name
		elif type_info == "h5pactivity":
			return session.get(MH5PActivity, self.instance).name
		elif type_info == "page":
			# Section hat ein Attribut name, dass modul selbst nicht
			return self.section.name
		elif type_info == "url":
			return session.get(MUrl, self.instance).name
		elif type_info == 'icecreamgame':
			return "Spiel zum Einstieg: Bestellen Sie Eis!"
		else: 
			return None
	
	def get_type_name(self, session: Session):
		#session.expire_all()
		return session.query(MModule).get(self._type_id).name

	# def get_availability_conditions(self, session: Session) -> bool:
		# TODO 

	def get_user_grade(self, user_id: int, session: Session) -> Union[MGradeGrade, None]:
		"""
		Returns:
			The associated grade item for the given user, or None if not applicable
			(Currently only works for h5pactivities)
		"""
		# check that the module is an h5pactivity
		if self.get_type_name(session) != 'h5pactivity':
			return None
		
		# get grade item id for this module (should only have 1 possible result)
		grade_item_id = session.query(MGradeItem).filter(MGradeItem.itemmodule=="hp5activity", MGradeItem._courseid==self._course_id,
														MGradeItem.itemtype=="mod", MGradeItem.iteminstance==self.instance) \
											   .first().id
		# get user grade for this grade item (should only have 1 possible result)
		return session.query(MGradeGrade).filter(MGradeGrade._gradeItemId==grade_item_id, MGradeGrade._userid==user_id).first()


	def get_branch_quizes_if_complete(self, session: Session, user_id: int) -> List["MCourseModule"]:
		"""
		Returns:
			The list of all quizes belonging to the same topic branch in the course, if the whole branch is completed
			e.g. (Branch A with sections 'Thema A:', 'Quizzes zum Thema A1-1:', ...)
		"""
		# figure out current branch
		matches = re_topic_branch.match(self.section.name)
		quizzes = []
		if matches:
			# extract topic letter
			topic_letter = matches.group(1) # e.g., A, B, ...
			# find all sections belonging to the same topic branch
			sections = session.query(MCourseSection).filter(MCourseSection._course_id==self._course_id,
												   			MCourseSection.name.contains(f"Thema {topic_letter}")).all()
			for section in sections:
				if not section.is_completed(user_id=user_id, session=session):
					# if section is not completed yet, return nothing
					return []
				if section.name.startswith("Quizzes"):
					# if we are in a quiz section, collect all the quizes
					for module in section.modules:
						if module.get_type_name(session) == "h5pactivity":
							quizzes.append(module)
		return quizzes


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
	summary = Column(Text)
	summaryformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
	availability = Column(Text) # input for is_available (json_condition)
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


	def is_quiz_section(self) -> bool:
		return "quiz" in self.name.lower()
	
	def _clean_name(self, name):
		if self.name == "Thema C1-1: Das Koordinatensystem - Was ist wo?":
			return self.name.replace(" - Was ist wo?", "")
		elif self.name == "Quizzes zum Thema C1-1: Das Koordinatensystem":
			return self.name + " - Was ist wo?"
		return self.name

	def get_quiz_section(self, session: Session) -> "MCourseSection":
		if self.is_quiz_section():
			return self
		# find related quiz section
		quiz_section_name =f"Quizzes zum {self._clean_name(self.name)}"
		return session.query(MCourseSection).filter(MCourseSection.name==quiz_section_name,
													  MCourseSection._course_id==self._course_id).first()
	
	def get_content_section(self, session: Session) -> "MCourseSection":
		if not self.is_quiz_section():
			return self
		# find related content section
		content_section_name = self._clean_name(self.name).replace("Quizzes zum ", "")
		return session.query(MCourseSection).filter(MCourseSection.name==content_section_name,
													  MCourseSection._course_id==self._course_id).first()

	def get_next_available_module(self, currentModule: MCourseModule, user: "MUser", session: Session, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz', 'url'], allow_only_unfinished: bool = False, currentModuleCompletion=None) -> Union[MCourseModule, None]:
		"""
		Given a current course module (e.g. the most recently finished one) in this course section,
		find the course module the student should do next.

		Args:
			currentModule: if None, will return first available module in section
			included_types: obtain e.g. via MCourseModule.get_type_name()
							PDF = resource
			allow_only_unfinished: if True, will filter for only course modules that were not completed by the user

		Returns: 
			MCourseModule (in order) that can be taken  after `currentModule`.
			Will return `None`, if no next module is defined for this section after `currentModule`.
		"""
		#session.expire_all()
		# print("SEQUENCE", self.sequence, 'name', self.name, 'id', self.id)
		unfinished_modules = []
		for index, moduleId in enumerate(self.sequence):
			# walk over all section modules
			next_module = session.get(MCourseModule, moduleId)
			if is_available_course_module(session, user.id, next_module) and next_module.get_type_name(session) in include_types:
				# only look at modules that are 1) available and 2) whitelisted by type
				# check module completion
				if currentModule and int(moduleId) == currentModule.id and not isinstance(currentModuleCompletion, type(None)):
					completed = currentModuleCompletion
				else:
					completed = next_module.is_completed(user.id, session)
				open_respecting_unfinished = ((allow_only_unfinished and not completed) or allow_only_unfinished == False)
				if open_respecting_unfinished and (not currentModule):
					# module not completed, and we don't give in a currentModule: return first module
					return next_module
				if not completed and int(moduleId) == currentModule.id:
					# module not completed, but it's the currentModule: return, because it still has to be finished
					return currentModule
				if not open_respecting_unfinished and int(moduleId) == currentModule.id:
					# module is the current module, and it has been completed:
					# get next module from section in sequence (if exists)
					# - if that hasen't been completed yet, return it
					if len(self.sequence) > index + 1:
						nextModuleId = int(self.sequence[index+1])
						next_module_candidate = session.get(MCourseModule, nextModuleId)
						completed = next_module_candidate.is_completed(user.id, session)
						open_respecting_unfinished_candidate = ((allow_only_unfinished and not completed) or allow_only_unfinished == False)
						if open_respecting_unfinished_candidate and next_module_candidate.get_type_name(session) in include_types:
							return next_module_candidate
				if open_respecting_unfinished:
					# keep track of all unfinished modules in the section
					unfinished_modules.append(next_module)
		if len(unfinished_modules) > 0:
			# we haven't returned from any of the conditions above, so just return 1st unfinished module
			return unfinished_modules[0]
		return None

	
	def get_first_available_module(self, user: "MUser", session: Session, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz'], allow_only_unfinished: bool = False) -> Union[MCourseModule, None]:
		"""
		Find the first course module in this section that is available.

		Args:
			included_types: obtain e.g. via MCourseModule.get_type_name()
							PDF = resource
			allow_only_unfinished: if True, will filter for only course modules that were not completed by the user

		Returns: 
			MCourseModule (in order) that can be taken  after `currentModule`.
			Will return `None`, if no next module is defined for this section after `currentModule`.
		"""
		#session.expire_all()
		# print("SEQUENCE", self.sequence, 'name', self.name, 'id', self.id)

		for nextModuleId in self.sequence:
			module = session.get(MCourseModule, nextModuleId)
			if is_available_course_module(session, user.id, module) and module.get_type_name(session) in include_types and ((allow_only_unfinished and not module.is_completed(user_id=user.id, session=session)) or allow_only_unfinished == False):
				return module
		return None
	
	def get_link(self):
		""" Get link to course section """
		return f'<a href="{MOODLE_SERVER_URL}/course/view.php?id={self._course_id}&section={self._section_id}">{self.name}</a>'

	def is_completed(self, user_id: int, session: Session, include_types=["url", "book", "resource", "quiz", "h5pactivity"]) -> bool:
		""" Query if user has completed this course section (= all course modules inside this course section).
			Users have to mark all activities inside this section as done manually.

		Args:
			user (MUser): the user to check completion for this course section

		Returns:
			completion state (bool): True, if user completed this course section, else False
		"""
		#session.expire_all()

		all_section_module_ids = set([module.id for module in self.modules if module.get_type_name(session) in include_types])

		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user_id).all()
		completed_section_module_ids = [completion._coursemoduleid for completion in completions if completion._coursemoduleid in all_section_module_ids]
		return len(all_section_module_ids.difference(completed_section_module_ids)) == 0
	
	def get_content_modules(self, session: Session, include_types=["url", "book", "resource", "quiz", "h5pactivity"]) -> List[MCourseModule]:
		"""
		Return the "Content" modules corresponding to the include types from this section.
		"""
		return [module for module in self.modules if module.get_type_name(session) in include_types]

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
	recently_accessed_items = relationship("MChatbotRecentlyAcessedItem", back_populates="course")

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
	intro = Column(Text, nullable=False)
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

	timecreated = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	progress = Column(Float, nullable=False)

	user = relationship("MUser", back_populates="progress", uselist=False) # user object

	# internal database mapping info
	_userid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}user.id'), nullable=False, index=True,
				   server_default=text("'0'"), name='userid', primary_key=True)



class MChatbotSettings(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}chatbot_settings"

	allow_auto_open = Column(BOOLEAN, nullable=False)
	preferred_content_fromat = Column(String(100, 'utf8mb4_bin'), nullable=True, index=True, server_default=text("''"))

	user = relationship("MUser", back_populates="settings", uselist=False) # user object

	# internal database mapping info
	_userid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}user.id'), nullable=False, index=True,
					   server_default=text("'0'"), name='userid', primary_key=True)


class MChatbotHistory(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}chatbot_history"

	id = Column(BIGINT(10), primary_key=True, autoincrement=True)
	timecreated = Column(UnixTimestamp)

	speaker = Column(Text)
	message = Column(Text)
	act = Column(Text)

	user = relationship("MUser", uselist=False) # user object

	# internal database mapping info
	_userid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}user.id'), nullable=False, index=True,
					   server_default=text("'0'"), name='userid', primary_key=True)



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


class MChatbotRecentlyAcessedItem(Base):
	__tablename__ = f'{MOODLE_SERVER_DB_TALBE_PREFIX}chatbot_recentlyaccessed'

	id = Column(BIGINT(10), primary_key=True)
	timeaccess = Column(UnixTimestamp, nullable=False, server_default=text("'0'"))
	completionstate = Column(TINYINT)

	user = relationship("MUser", back_populates="recently_accessed_items", uselist=False) # user object
	coursemodule = relationship("MCourseModule", back_populates="recently_accessed_items", uselist=False)
	course = relationship("MCourse", back_populates="recently_accessed_items", uselist=False)
	

	# internal database mapping info
	_userid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}user.id'), nullable=False, index=True, server_default=text("'0'"), name='userid')
	_course_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), name='courseid')
	_coursemodule_id = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules.id'), index=True, name='cmid')


class MLabel(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}label"

	id = Column(BIGINT(10), primary_key=True)
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	intro =  Column(Text)

	_courseid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), name='courseid')




class MBadge(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}badge"

	id = Column(BIGINT(10), primary_key=True)
	name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	description = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
	status = Column(BadgeStatus, nullable=False)

	criteria = relationship("MBadgeCriteria", back_populates="badge")

	_courseid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course.id'), name='courseid')


	# badge conditions:
	# 1. badge nicht gemacht (vorraussetzungen fehlen) -> suche fehlende module
	# 2. badge nicht claimed, aber alle vorraussetzungen gemacht (außer manuell auf abgeschlossen zu Klicken) -> check ob label.is_available() -> link ausgeben
	# 3. badge ist claimed -> in tabelle badge_issued -> warte auf Event und sag herzlichen glückwunsch

	def is_completed(self, session: Session, user_id: int, crit: "MBadgeCriteria") -> BadgeCompletionStatus:
		if session.query(MBadgeIssued).filter(MBadgeIssued._userid==user_id, MBadgeIssued._badgeid==self.id).count() > 0:
			# badge	is already claimed, no need to check further
			return BadgeCompletionStatus.CLAIMED
		# badge is not claimed yet, check if all requirements are completed
		if len(crit.criteria_params) == 1 and crit.criteria_params[0].module.get_type_name(session) == "label":
			# badge is a label - and all the requirements for this label are fulfilled
			if is_available_course_module(session=session, user_id=user_id, course_module=crit.criteria_params[0].module):
				return BadgeCompletionStatus.COMPLETED
		# badge is neither claimed, nor are its requirements met fully
		return BadgeCompletionStatus.INCOMPLETE

	def is_available(self, session: Session, user_id: int) -> bool:
		"""
		Returns:
			True, if all requirements for the badge are available to the user
		"""
		# there should only be ONE possible criterium (either method=all or method=any) for this badge
		crit = self.get_activity_criterion(session=session)
		# collect progress towards completion criteria
		for param in crit.criteria_params:
			if not is_available_course_module(session=session, user_id=user_id, course_module=param.module):
				return False
		return True
			

	def _completed_bronze_silver_or_gold(self, session: Session, user_id: int) -> bool:
		# these badges are a single outlier in their configuration and not worth checking all the grading
		return True
		# bronze_badge = session.query(MBadge).filter(MBadge.name.startswith("Bronzemedaille Regression"), MBadge._courseid==self._courseid).first()
		# silver_badge = session.query(MBadge).filter(MBadge.name.startswith("Silbermedaille Regression"), MBadge._courseid==self._courseid).first()
		# gold_badge = session.query(MBadge).filter(MBadge.name.startswith("Bronzemedaille Regression"), MBadge._courseid==self._courseid).first()
		# return any([bronze_badge.is_completed(session=session, user_id=user_id, crit=bronze_badge.get_activity_criterion(session)),
		# 	  		silver_badge.is_completed(session=session, user_id=user_id, crit=silver_badge.get_activity_criterion(session)),
		# 			gold_badge.is_completed(session=session, user_id=user_id, crit=gold_badge.get_activity_criterion(session))])
		

	def get_activity_criterion(self, session: Session) -> Tuple[None, "MBadgeCriteria"]:
		"""
		Returns: The badge criterion for activity completion (not manual completion).
				 There should be at most 1 possibility.
		"""
		return session.query(MBadgeCriteria).filter(MBadgeCriteria.criteriatype==1,
													MBadgeCriteria._badgeid==self.id).first()


	def criteria_completion_percentage(self, session: Session, user_id: int) -> Tuple[float, BadgeCompletionStatus, List["MCourseModule"]]:
		"""
		Returns:
			The completion towards this badge in percent.
			Also returns a list of missing course modules in order to achieve the badge.

		"""

		# there should only be ONE possible criterium (either method=all or method=any) for this badge
		crit = self.get_activity_criterion(session=session)
		if not crit:
			return (0.0, BadgeCompletionStatus.INCOMPLETE, [])
		
		# if badge is already completed, return 100% and no todo modules
		completed = self.is_completed(session=session, user_id=user_id, crit=crit)
		if completed in [BadgeCompletionStatus.CLAIMED, BadgeCompletionStatus.COMPLETED]:
			return (1.0, completed, []) 
		
		# special case for regression (has 3 associated badges: bronze, silver and gold)
		# -> should be enough to get one
		if "medaille Regression" in self.name:
			if self._completed_bronze_silver_or_gold(session=session, user_id=user_id):
				return (1.0, BadgeCompletionStatus.COMPLETED, [])
			else:
				# get regression quiz section
				section_regression = session.query(MCourseSection).filter(MCourseSection._course_id==self._courseid,
															  			MCourseSection.name=="Quizzes zum Thema A1-1: Regression").first()
				if not section_regression:
					# teacher altered section - give up by pretending badge was earned
					return (1.0, BadgeCompletionStatus.CLAIMED, [])
				# get completion of each quiz in regression quiz section
				todo_modules = []
				param_eval = []
				for module in section_regression.modules:
					if module.get_type_name(session) == "h5pactivity":
						if module.is_completed(user_id=user_id, session=session):
							param_eval.append(True)
						else:
							param_eval.append(False)
							todo_modules.append(module)
				percentage_done = 1 - len(todo_modules) / len(param_eval)
				return (percentage_done, BadgeCompletionStatus.INCOMPLETE, todo_modules)


		# collect progress towards completion criteria
		todo_modules = []
		param_eval = []
		for param in crit.criteria_params:
			# skip labels
			# TODO  and is_available_course_module(session, self.id, module) -> check section complete, or individual modules?
			# in the second case, we still need to handle 0 todo_modules extra
			if param.module.get_type_name(session) != "label":
				if param.module.is_completed(user_id=user_id, session=session):
					param_eval.append(True)
				else:
					param_eval.append(False)
					todo_modules.append(param.module)

		# evaluate progress
		if crit.method == BadgeMethodEnum.AGGREGATION_ANY:
			# no entry in param_eval can be True, otherwise the bade would already have been issued
			# -> this also means: progress is 0!
			# return a random choice from the possible completion options (because there can be multiple, but completing 1 is enough)
			if len(todo_modules) > 0:
				return (0.0, BadgeCompletionStatus.INCOMPLETE, [random.choice(todo_modules)])
			else:
				# this is probably a new badge for an existing user that already has the requirements, but never got the badge issued
				return (1.0, BadgeCompletionStatus.COMPLETED, [])
		else:
			percentage_done = 1 - len(todo_modules) / len(param_eval)
			return (percentage_done, BadgeCompletionStatus.INCOMPLETE, todo_modules)


class MBadgeCriteria(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}badge_criteria"	

	id = Column(BIGINT(10), primary_key=True)
	# CRITERIA TYPE = 1 (0 = Manual, 1 = Activity completion) -> we are only interested in 1
	criteriatype = Column(TINYINT(2), nullable=False)
	method = Column(BadgeMethod, nullable=False)

	badge = relationship("MBadge", back_populates="criteria", uselist=False)
	criteria_params = relationship("MBadgeCriteriaParam", back_populates="criterium")

	_badgeid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}badge.id'), name='badgeid')


class MBadgeCriteriaParam(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}badge_criteria_param"	

	id = Column(BIGINT(10), primary_key=True)

	module = relationship("MCourseModule", uselist=False)
	criterium = relationship("MBadgeCriteria", back_populates="criteria_params", uselist=False)
	
	_moduleid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}course_modules.id'), name='value')
	_critid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}badge_criteria.id'), name='critid')	

class MBadgeIssued(Base):
	__tablename__ = f"{MOODLE_SERVER_DB_TALBE_PREFIX}badge_issued"	

	id = Column(BIGINT(10), primary_key=True)
	dateissued = Column(UnixTimestamp)

	_badgeid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}badge.id'), name='badgeid')
	_userid = Column(BIGINT(10), ForeignKey(f'{MOODLE_SERVER_DB_TALBE_PREFIX}user.id'), name="userid")	


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
	# chatbot settings
	settings = relationship("MChatbotSettings", back_populates="user", uselist=False)
	progress = relationship("MChatbotProgressSummary", back_populates="user", uselist=False)
	recently_accessed_items = relationship("MChatbotRecentlyAcessedItem", back_populates="user", uselist=True)

	def get_closest_badge(self, session: Session, courseid: int) -> Union[Tuple[MBadge, float, BadgeCompletionStatus, List[MCourseModule]], None]:
		"""
		Returns:
			Closest uncompleted badge, the progress towards it, and the modules still needed to get it.
			None, if all badges are completed.
		"""
		# get ids of regression badges to exclude from suggestions
		bronze_badge = session.query(MBadge).filter(MBadge.name.startswith("Bronzemedaille Regression"), MBadge._courseid==courseid).first()
		silver_badge = session.query(MBadge).filter(MBadge.name.startswith("Silbermedaille Regression"), MBadge._courseid==courseid).first()
		gold_badge = session.query(MBadge).filter(MBadge.name.startswith("Goldmedaille Regression"), MBadge._courseid==courseid).first()

		# get badges that are not issued
		closed_badge_ids = [badge._badgeid for badge in session.query(MBadgeIssued).filter(MBadgeIssued._userid==self.id).all()] + \
							[bronze_badge.id, silver_badge.id, gold_badge.id]
		# get all open badges
		open_badges = session.query(MBadge).filter(MBadge.id.not_in(closed_badge_ids), MBadge._courseid==courseid).all()
		# sort out all badges that are not available yet
		open_badges = list(filter(lambda badge: badge.is_available(session=session,user_id=self.id), open_badges))
		# sort available open badges by progress (descending)
		badge_completion_progress = sorted([(badge, *badge.criteria_completion_percentage(session=session, user_id=self.id)) for badge in open_badges], key=lambda p: p[1], reverse=True)
		if len(badge_completion_progress) > 0:
			# return closest badge
			return badge_completion_progress[0]
		return None


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

	def get_all_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> List[MCourseModule]:
		""" Return all course modules already completed by current user in the specified course """
		#session.expire_all()
		coursemodules = session.query(MCourseModule).filter(MCourseModule._course_id==courseid)
		return [coursemodule for coursemodule in coursemodules if coursemodule.get_type_name(session) in include_types]

	def get_completed_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz'], timerange: List[int] = None) -> List[MCourseModulesCompletion]:
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

	def get_viewed_course_modules(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz'], timerange: List[int] = None) -> List[MCourseModulesCompletion]:
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


	def is_completed(self, session: Session, module_id: int ,courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> bool:
		""" Return wheteher a module  is completed by this user or not """
		#session.expire_all()
		completions = self.get_completed_course_modules(session, courseid, include_types)
		for completion in completions:
			if module_id == completion.id:
				return True
		return False

	def get_completed_course_modules_before_date(self, date, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> List[MCourseModulesCompletion]:
		""" Return all course modules already completed by current user before a date """
		#session.expire_all()
		completions = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True)
		return [completion.coursemodule for completion in completions if completion.coursemodule.get_type_name(session) in include_types and completion.coursemodule._course_id==courseid]

	def get_not_finished_courses_before_date(self, date, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> List[MCourseModulesCompletion]:
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
		quiz_types = session.query(MModule).filter((MModule.name=='h5pactitivty')).all() # TODO re-enable at some point? | (MModule.name=="quiz")).all()
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
		quiz_types = session.query(MModule).filter((MModule.name=='h5pactitivty')).all() # TODO re-enable at some point? | (MModule.name=="quiz")).all()
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
	def get_last_completed_coursemodule(self, session: Session, courseid: int, current_server_time: datetime.datetime, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> Union[MCourseModule, None]:
		""" Get the course module the current user completed most recently.
			If there is no completed module yet, return the first one
		Returns:
			* last completed course module (MCourseModule), if the user already completed any course module, else `None`
		"""
		#session.expire_all()
		completions: List[MCourseModulesCompletion] = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True).all()
		
		completions = list(filter(lambda comp: comp.coursemodule.get_type_name(session) in include_types and comp.coursemodule._course_id==courseid, completions))

		if len(completions) == 0:
			available_modules = self.get_available_course_modules(session, courseid=courseid, current_server_time=current_server_time)
			if len(available_modules) == 0:
				return available_modules[0] # return first result
			else:
				return None
		return max(completions, key=lambda comp: comp.timemodified).coursemodule

	def get_last_completed_quiz(self, session: Session, courseid: int, current_server_time: datetime.datetime) -> Union[MCourseModule, None]:
		""" Get the course module the current user completed most recently.
			If there is no completed module yet, return the first one
		Returns:
			* last completed course module (MCourseModule), if the user already completed any course module, else `None`
		"""
		#session.expire_all()
		completions: List[MHVP] = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True).all()
		completions = [completion for completion in completions if completion.coursemodule._course_id==courseid]
		if len(completions) == 0:
			return self.get_available_course_modules(session, courseid=courseid, current_server_time=current_server_time)[0] # return first result
		return max(completions, key=lambda comp: comp.timemodified).coursemodule

	def get_not_completed_courses(self, session: Session, courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> List[MCourseModule]:
		""" Return all course modules not completed by current user """
		#session.expire_all()
		completed = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==self.id, MCourseModulesCompletion.completed==True)
		completed_ids = [complete._coursemoduleid for complete in completed if complete.coursemodule.get_type_name(session) in include_types and complete.coursemodule._course_id==courseid]
		courses = session.query(MCourseModule).all()
		return [course for course in courses if course.id not in completed_ids]

	def get_available_course_modules(self, session: Session, courseid: int, current_server_time: datetime.datetime, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> List[MCourseModule]:
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if is_available_course_sections(session, self.id, section, current_server_time):
				for course_moudule in section.modules:
					if is_available_course_module(session, self.id, course_moudule) and course_moudule.get_type_name(session) in include_types:
						available.append(course_moudule)
		return available

	def get_available_new_course_sections(self, session: Session, courseid: int, current_server_time: datetime.datetime) -> List[MCourseSection]:
		""" Returns all course sections the user can start (according to section requirements),
			exluding already completed sections
		"""
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if is_available_course_sections(session, self.id, section, current_server_time) and not section.is_completed(self.id, session):
				some_modules_not_available = any([not is_available_course_module(session, self.id, module) for module in section.get_content_modules(session=session)])
				if not some_modules_not_available:
					available.append(section)
		return available

	def get_incomplete_available_course_modules(self, session: Session, courseid: int, current_server_time: datetime.datetime, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> List[MCourseModule]:
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if is_available_course_sections(session, self.id, section, current_server_time):
				for course_moudule in section.modules:
					if not course_moudule.is_completed(self.id, session) and is_available_course_module(session, self.id, course_moudule) and course_moudule.get_type_name(session) in include_types:
						available.append(course_moudule)
		return available		
	
	def get_incomplete_available_course_sections(self, session: Session, courseid: int, current_server_time: datetime.datetime) -> List[MCourseSection]:
		#session.expire_all()
		available = []
		for section in session.query(MCourseSection).filter(MCourseSection._course_id==courseid):
			if (not section.is_completed(self.id, session) and is_available_course_sections(session, self.id, section, current_server_time) 
				and section.name and not section.name.lower().startswith("ki und maschinelles lernen") 
				and not section.name.lower().startswith("nicht-finale version")  and not section.name.lower().startswith("spiel zum einstieg")):
				available.append(section)
		return available
	
	def last_viewed_course_modules(self, session: Session, courseid: int, completed: bool = True) -> List[MCourseModule]:
		"""
		Returns the last viewed course module by the current user (that is completed, if completed = True),
		or an empty list, if the user has not yet accessed any course module (or not completed any)
		"""
		return [item.coursemodule for item in session.query(MChatbotRecentlyAcessedItem)
												.filter(MChatbotRecentlyAcessedItem._course_id==courseid, 
														MChatbotRecentlyAcessedItem.completionstate==int(completed),
														MChatbotRecentlyAcessedItem._userid==self.id)
				.order_by(desc(MChatbotRecentlyAcessedItem.timeaccess)).all()]
	

	def recent_incomplete_sections(self, session: Session, courseid: int) -> List[MCourseSection]:
		incomplete_sections = []
		recently_accessed = session.query(MChatbotRecentlyAcessedItem).filter(MChatbotRecentlyAcessedItem._course_id==courseid, MChatbotRecentlyAcessedItem._userid==self.id).all()
		section_ids_viewed = set()
		for recent_access in recently_accessed:
			section = recent_access.coursemodule.section
			if section.id in section_ids_viewed:
				continue # we already checked
			section_ids_viewed.add(section.id)
			if not section.is_completed(self.id, session):
				incomplete_sections.append(section)
		return incomplete_sections


	def __repr__(self) -> str:
		""" Pretty printing """
		return f"""User {self.username} ({self.id})
			- Last login: {self.lastlogin}
			- Last accessed course: {self.last_accessed_course.course if self.last_accessed_course else None}
		"""
		# - Grades: {self.get_grades()}


def _recursive_availability(session: Session, json_tree: dict, user_id: int, current_server_time: datetime.datetime) -> bool:
	condition_values = []
	for condition in json_tree["c"]:
		if "c" in condition:
			# nested condition
			condition_values.append(_recursive_availability(session, condition, user_id, current_server_time))
		else:
			if condition['type'] == "completion":
				completed = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._coursemoduleid==condition['cm'], 
																		   MCourseModulesCompletion._userid==user_id,
																		   MCourseModulesCompletion.completed==1).count() > 0
				condition_values.append(condition['e']==completed)
			elif condition['type'] == "grade":
				grade = session.query(MGradeGrade).filter(MGradeGrade._userid==user_id,MGradeGrade._gradeItemId==condition['id']).first()
				if grade and not (grade.finalgrade is None):
					if "min" in condition:
						condition_values.append(grade.finalgrade >= condition["min"])
					elif "max" in condition:
						condition_values.append(grade.finalgrade <= condition["max"])
				else:
					condition_values.append(False)
			elif condition['type'] == "date":
				assert NotImplementedError
				# date = datetime.datetime.fromtimestamp(condition['t'])
				# server_date = datetime.datetime.now() + server_timedelta
				# if condition['d'] == ">":
				#     condition_values.append(current_server_time > server_date)
				# elif condition['d'] == ">=":
				#     condition_values.append(current_server_time >= server_date)
				# elif condition['d'] == "==":
				#     condition_values.append(current_server_time == server_date)
				# elif condition['d'] == "<=":
				#     condition_values.append(current_server_time <= server_date)
				# elif condition['d'] == "<":
				#     condition_values.append(current_server_time < server_date)
	if len(condition_values) == 0:
		# no conditions found
		return True
	return any(condition_values) if json_tree["op"]=="|" else all(condition_values) 



def is_available(json_condition: str, session: Session, user_id: int, current_server_time: datetime.datetime) -> bool:
	#session.expire_all()
	if not json_condition:
		return True # no restrictions

	data = json.loads(json_condition)
	if not data['c']:
		return True # no restrictions

	# check conditions
	return _recursive_availability(session=session, json_tree=data, user_id=user_id, current_server_time=current_server_time)


def is_available_course_module(session: Session, user_id: int, course_module: MCourseModule, current_server_time: datetime.datetime = None):
	section = course_module.section
	if section.is_quiz_section():
		# some quiz sections are available, even though the content section is not.
		# this fixes it.
		content_section = section.get_content_section(session)
		if (not isinstance(content_section, type(None))) and (not is_available_course_sections(session=session, user_id=user_id, section=content_section, current_server_time=current_server_time)):
			return False
	else:
		# some content sections are available, even though the quiz section is not.
		# this fixes it.
		quiz_section = section.get_quiz_section(session)
		if (not isinstance(quiz_section, type(None))) and (not is_available_course_sections(session=session, user_id=user_id, section=quiz_section, current_server_time=current_server_time)):
			return False
	# sections are available, check module availability
	return bool(course_module.visible) and is_available(json_condition=course_module.availability, session=session, user_id=user_id, current_server_time=None)


def is_available_course_sections(session: Session, user_id: int, section: MCourseSection, current_server_time: datetime.datetime = None):
	#session.expire_all()
	if section.is_quiz_section():
		# check if materials were already viewed, otherwise don't suggest quizzes
		return section.get_content_section(session).is_completed(user_id=user_id, session=session)
	return bool(section.visible) and is_available(json_condition=section.availability, session=session, user_id=user_id, current_server_time=current_server_time)




def get_time_estimate_module(session: Session, user: MUser, course_module: MCourseModule) -> Union[int, None]:
	#session.expire_all()
	already_completed = session.query(MCourseModulesCompletion).filter(MCourseModulesCompletion._userid==user.id)
	if is_available_course_module(session, user.id, course_module) and already_completed.filter(MCourseModulesCompletion._coursemoduleid==course_module.id).count() == 0:
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

def get_time_estimates(session: Session, user: MUser, courseid: int, include_types: List[str] = ['assign', 'book', 'h5pactitivty',  'quiz']) -> List[Tuple[MCourseModule, int]]:
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




# # connect to database
# from sqlalchemy.orm import sessionmaker
# import traceback
# engine, conn = connect_to_moodle_db()
# Session = sessionmaker()
# Session.configure(bind=engine)
# Base.metadata.create_all(engine)


# with Session() as session:
# 	for badge in session.query(MBadge).filter(MBadge._courseid==2).all():
# 		print("-----------")
# 		print(badge.name)
# 		progress, status, todo_modules = badge.criteria_completion_percentage(session=session, user_id=2)
# 		print("Progress: ", progress * 100)
# 		if progress < 1:
# 			print("TODO:")
# 			for todo_module in todo_modules:
# 				print(" - ", todo_module.get_name(session))
# conn.close()