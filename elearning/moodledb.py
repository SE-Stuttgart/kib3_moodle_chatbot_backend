# coding: utf-8
import datetime
import httplib2
from dataclasses import dataclass
import json
from typing import Dict, List, Tuple, Union
import urllib

from config import MOODLE_SERVER_WEB_HOST, MOOLDE_SERVER_PROTOCOL


@dataclass
class UserSettings:
	userid: int
	preferedcontenttype: str
	preferedcontenttypeid: int

	enabled: bool
	firstturn: bool
	logging: bool
	numsearchresults: int
	numreviewquizzes: int
	
	openonlogin: bool
	openonquiz: bool
	openonsection: bool
	openonbranch: bool
	openonbadge: bool

@dataclass
class ModuleReview:
	cmid: int
	grade: Union[float, None]

@dataclass
class BranchReviewQuizzes:
	completed: bool
	branch: str # branch topic letter
	candidates: List[ModuleReview]

@dataclass
class CourseModuleAccess:
	cmid: int
	section: int
	timeaccess: datetime.datetime
	completionstate: int

@dataclass
class UserStatistics:
	course_completion_percentage: float
	quiz_repetition_percentage: float

@dataclass
class WeeklySummary:
	first_turn_ever: bool
	first_week: bool
	timecreated: datetime.datetime
	course_progress_percentage: float

@dataclass
class BadgeCompletionInfo:
	id: int
	name: str
	completion_percentage: float
	open_modules: List[int]

@dataclass
class BadgeInfo:
	id: int
	name: str
	url: str # url to badge image

@dataclass
class H5PQuizParameters:
	host: str
	context: int
	filearea: str
	itemid: int
	filename: str

	def serialize(self) -> dict:
		return {
			"host": self.host,
			"context": self.context,
			"filearea": self.filearea,
			"itemid": self.itemid,
			"filename": self.filename
		}


@dataclass
class QuizInfo:
	cmid: int
	grade: float

@dataclass
class SectionInfo:
	id: int # section id
	section: int # index of section in course
	url: str
	name: str
	firstcmid: int

@dataclass
class ContentLinkInfo:
	url: str
	name: str
	typename : str

	def to_dict(self, alternative_displayname: str = None) -> Dict[str, str]:
		return {
			"url": self.url,
			"displaytext": self.name if alternative_displayname is None else alternative_displayname,
			"typename": self.typename
		}

def api_call(wstoken: str, wsfunction: str, params: dict):
	http_client = httplib2.Http(".cache", disable_ssl_certificate_validation=True)
	body={
			"wstoken": wstoken,
			"wsfunction": wsfunction,
			"moodlewsrestformat": "json",
			**params
	}
	response = http_client.request(f"{MOOLDE_SERVER_PROTOCOL}://{MOODLE_SERVER_WEB_HOST}/webservice/rest/server.php",
		method="POST",
		headers={'Content-type': 'application/x-www-form-urlencoded'},
		body=urllib.parse.urlencode(body))[1] # result is binary string with escaped quotes -> decode
	response = response.strip()
	# print("response: ", response)
	start_pos = 0
	end_pos = len(response)
	if response.startswith(b"<script"):
		# remove debugging console log from response
		start_pos = response.rfind(b"</script>") + len(b"</script>")
	
	# Extracst the JSON part
	json_part = response[start_pos:end_pos + 1]
	# Decode the JSON part and parse it
	data = json.loads(json_part.decode().strip('"').replace("\\/", "/").replace('\/', '/'))

	return data


def fetch_user_settings(wstoken: str, userid: int) -> UserSettings:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_usersettings", params=dict(userid=userid))
	assert response['userid'] == userid
	return UserSettings(**response)

def fetch_branch_review_quizzes(wstoken: str, userid: int, sectionid: int) -> BranchReviewQuizzes:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_branch_quizes_if_complete", params=dict(
		userid=userid,
		sectionid=sectionid,
		includetypes="url,book,resource,h5pactivity,quiz"
	))
	branch_completed = response['completed']
	cm_candidates = []
	for candidate in response['candidates']:
		cm_candidates.append(ModuleReview(**candidate))
	return BranchReviewQuizzes(completed=branch_completed, candidates=cm_candidates, branch=response['branch'])

def fetch_section_id_and_name(wstoken: str, cmid: int) -> Tuple[int, str]:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_section_id", params=dict(
		cmid=cmid
	))
	return response['id'], response['name']

def fetch_section_completionstate(wstoken: str, userid: int, sectionid: int, includetypes: str = "url,book,resource,h5pactivity,quiz,icecreamgame") -> bool:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_section_completionstate", params=dict(
		userid=userid,
		sectionid=sectionid,
		includetypes=includetypes
	))
	return response['completed']

def fetch_has_seen_any_course_modules(wstoken: str, userid: int, courseid: int) -> bool:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_has_seen_any_course_modules", params=dict(
		userid=userid,
		courseid=courseid
	))
	return response['seen']

def fetch_last_viewed_course_modules(wstoken: str, userid: int, courseid: int, completed: bool, includetypes: str = "url,book,resource,h5pactivity,quiz,icecreamgame") -> List[CourseModuleAccess]:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_last_viewed_course_modules", params=dict(
		userid=userid,
		courseid=courseid,
		completed=int(completed),
		includetypes=includetypes
	))
	results = []
	for result in response:
		results.append(CourseModuleAccess(
			timeaccess=datetime.datetime.utcfromtimestamp(result.pop('timeaccess')),
			**result
		))
	return results

def fetch_first_available_course_module_id(wstoken: str, userid: int, courseid: int, sectionid: int, includetypes: str = "url,book,resource,h5pactivity,quiz,icecreamgame", allow_only_unfinished: bool = False) -> Union[int, None]:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_first_available_course_module", params=dict(
		userid=userid,
		courseid=courseid,
		sectionid=sectionid,
		includetypes=includetypes,
		allowonlyunfinished=int(allow_only_unfinished)
	))
	return response['cmid']

def fetch_content_link(wstoken: str, cmid: int) -> ContentLinkInfo:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_course_module_content_link", params=dict(
		cmid=cmid,
	))
	return ContentLinkInfo(**response)

def fetch_available_new_course_section_ids(wstoken: str, userid: int, courseid: int) -> List[SectionInfo]:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_available_new_course_sections", params=dict(
		userid=userid,
		courseid=courseid
	))
	return filter(lambda info: info.firstcmid is not None, [SectionInfo(**res) for res in response])

def fetch_icecreamgame_course_module_id(wstoken: str, courseid: int) -> int:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_icecreamgame_course_module_id", params=dict(
		courseid=courseid
	))
	return response['id']

def fetch_next_available_course_module_id(wstoken: str, userid: int, current_cmid: int, include_types: str = "url,book,resource,h5pactivity,quiz,icecreamgame", allow_only_unfinished: bool = False, current_cm_completion: int = 0) -> int:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_next_available_course_module_id", params=dict(
		userid=userid,
		cmid=current_cmid,
		includetypes=include_types,
		allowonlyunfinished=int(allow_only_unfinished),
		currentcoursemodulecompletion=int(current_cm_completion)
	))
	return response['cmid']

def fetch_viewed_course_modules_count(wstoken: str, userid: int, courseid: int, include_types: str, starttime: datetime.datetime, endtime: datetime.datetime) -> int:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_count_completed_course_modules", params=dict(
		userid=userid,
		courseid=courseid,
		includetypes=include_types,
		starttime='{:.0f}'.format(starttime.timestamp()),
		endtime='{:.0f}'.format(endtime.timestamp())
	))
	return response['count']

def fetch_user_statistics(wstoken: str, userid: int, courseid: int, include_types: str = "url,book,resource,h5pactivity,icecreamgame", update_db: bool = False) -> UserStatistics:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_user_statistics", params=dict(
		userid=userid,
		courseid=courseid,
		includetypes=include_types,
		updatedb=int(update_db)
	))
	return UserStatistics(**response)

def fetch_last_user_weekly_summary(wstoken: str, userid: int, courseid: int, include_types: str = "url,book,resource,h5pactivity,icecreamgame", update_db: bool = False) -> WeeklySummary:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_last_user_weekly_summary", params=dict(
		userid=userid,
		courseid=courseid,
		includetypes=include_types,
		updatedb=int(update_db)
	))
	return WeeklySummary(
		timecreated=datetime.datetime.utcfromtimestamp(response.pop('timecreated')),
		**response
	)

def fetch_closest_badge(wstoken: str, userid: int, courseid: int) -> BadgeCompletionInfo:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_closest_badge", params=dict(
		userid=userid,
		courseid=courseid,
	))
	return BadgeCompletionInfo(**response)

def fetch_badge_info(wstoken: str, badgeid: int, contextid: int) -> BadgeInfo:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_badge_info", params=dict(
		badgeid=badgeid,
		contextid=contextid
	))
	return BadgeInfo(**response)

def fetch_h5pquiz_params(wstoken: str, cmid: int) -> H5PQuizParameters:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_h5pquiz_params", params=dict(
		cmid=cmid
	))
	return H5PQuizParameters(**response)

def fetch_oldest_worst_grade_course_ids(wstoken: str, userid: int, courseid: int, max_num_quizzes: int) -> List[QuizInfo]:
	response = api_call(wstoken=wstoken, wsfunction="block_chatbot_get_oldest_worst_grade_attempts", params=dict(
		userid=userid,
		courseid=courseid,
		max_results=max_num_quizzes
	))
	return [QuizInfo(**res) for res in response]

