# coding: utf-8
from sqlalchemy import Column, DECIMAL, Float, Index, String, text, create_engine
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, LONGTEXT, MEDIUMINT, SMALLINT, TINYINT
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus as urlquote
from sqlalchemy.orm import sessionmaker


Base = declarative_base()
metadata = Base.metadata


class MAnalyticsIndicatorCalc(Base):
    __tablename__ = 'm_analytics_indicator_calc'
    __table_args__ = (
        Index('m_analindicalc_staendcon_ix', 'starttime', 'endtime', 'contextid'),
        {'comment': 'Stored indicator calculations'}
    )

    id = Column(BIGINT(10), primary_key=True)
    starttime = Column(BIGINT(10), nullable=False)
    endtime = Column(BIGINT(10), nullable=False)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    sampleorigin = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sampleid = Column(BIGINT(10), nullable=False)
    indicator = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(DECIMAL(10, 2))
    timecreated = Column(BIGINT(10), nullable=False)


class MAnalyticsModel(Base):
    __tablename__ = 'm_analytics_models'
    __table_args__ = (
        Index('m_analmode_enatra_ix', 'enabled', 'trained'),
        {'comment': 'Analytic models.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    trained = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    name = Column(String(1333, 'utf8mb4_bin'))
    target = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    indicators = Column(LONGTEXT, nullable=False)
    timesplitting = Column(String(255, 'utf8mb4_bin'))
    predictionsprocessor = Column(String(255, 'utf8mb4_bin'))
    version = Column(BIGINT(10), nullable=False)
    contextids = Column(LONGTEXT)
    timecreated = Column(BIGINT(10))
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)


class MAnalyticsModelsLog(Base):
    __tablename__ = 'm_analytics_models_log'
    __table_args__ = {'comment': 'Analytic models changes during evaluation.'}

    id = Column(BIGINT(10), primary_key=True)
    modelid = Column(BIGINT(10), nullable=False, index=True)
    version = Column(BIGINT(10), nullable=False)
    evaluationmode = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    target = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    indicators = Column(LONGTEXT, nullable=False)
    timesplitting = Column(String(255, 'utf8mb4_bin'))
    score = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    info = Column(LONGTEXT)
    dir = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)


class MAnalyticsPredictSample(Base):
    __tablename__ = 'm_analytics_predict_samples'
    __table_args__ = (
        Index('m_analpredsamp_modanatimran_ix', 'modelid', 'analysableid', 'timesplitting', 'rangeindex'),
        {'comment': 'Samples already used for predictions.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    modelid = Column(BIGINT(10), nullable=False, index=True)
    analysableid = Column(BIGINT(10), nullable=False)
    timesplitting = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    rangeindex = Column(BIGINT(10), nullable=False)
    sampleids = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAnalyticsPredictionAction(Base):
    __tablename__ = 'm_analytics_prediction_actions'
    __table_args__ = (
        Index('m_analpredacti_preuseact_ix', 'predictionid', 'userid', 'actionname'),
        {'comment': 'Register of user actions over predictions.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    predictionid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    actionname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)


class MAnalyticsPrediction(Base):
    __tablename__ = 'm_analytics_predictions'
    __table_args__ = (
        Index('m_analpred_modcon_ix', 'modelid', 'contextid'),
        {'comment': 'Predictions'}
    )

    id = Column(BIGINT(10), primary_key=True)
    modelid = Column(BIGINT(10), nullable=False, index=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    sampleid = Column(BIGINT(10), nullable=False)
    rangeindex = Column(MEDIUMINT(5), nullable=False)
    prediction = Column(DECIMAL(10, 2), nullable=False)
    predictionscore = Column(DECIMAL(10, 5), nullable=False)
    calculations = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timestart = Column(BIGINT(10))
    timeend = Column(BIGINT(10))


class MAnalyticsTrainSample(Base):
    __tablename__ = 'm_analytics_train_samples'
    __table_args__ = (
        Index('m_analtraisamp_modanatim_ix', 'modelid', 'analysableid', 'timesplitting'),
        {'comment': 'Samples used for training'}
    )

    id = Column(BIGINT(10), primary_key=True)
    modelid = Column(BIGINT(10), nullable=False, index=True)
    analysableid = Column(BIGINT(10), nullable=False)
    timesplitting = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sampleids = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAnalyticsUsedAnalysable(Base):
    __tablename__ = 'm_analytics_used_analysables'
    __table_args__ = (
        Index('m_analusedanal_modact_ix', 'modelid', 'action'),
        {'comment': 'List of analysables used by each model'}
    )

    id = Column(BIGINT(10), primary_key=True)
    modelid = Column(BIGINT(10), nullable=False, index=True)
    action = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    analysableid = Column(BIGINT(10), nullable=False, index=True)
    firstanalysis = Column(BIGINT(10), nullable=False)
    timeanalysed = Column(BIGINT(10), nullable=False)


class MAnalyticsUsedFile(Base):
    __tablename__ = 'm_analytics_used_files'
    __table_args__ = (
        Index('m_analusedfile_modactfil_ix', 'modelid', 'action', 'fileid'),
        {'comment': 'Files that have already been used for training and predictio'}
    )

    id = Column(BIGINT(10), primary_key=True)
    modelid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    fileid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    action = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    time = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssign(Base):
    __tablename__ = 'm_assign'
    __table_args__ = {'comment': 'This table saves information about an instance of mod_assign'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    alwaysshowdescription = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    nosubmissions = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    submissiondrafts = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    sendnotifications = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    sendlatenotifications = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    duedate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    allowsubmissionsfromdate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    grade = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    requiresubmissionstatement = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    completionsubmit = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    cutoffdate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    gradingduedate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    teamsubmission = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    requireallteammemberssubmit = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    teamsubmissiongroupingid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    blindmarking = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    hidegrader = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    revealidentities = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    attemptreopenmethod = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("'none'"))
    maxattempts = Column(MEDIUMINT(6), nullable=False, server_default=text("'-1'"))
    markingworkflow = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    markingallocation = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    sendstudentnotifications = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    preventsubmissionnotingroup = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MAssignGrade(Base):
    __tablename__ = 'm_assign_grades'
    __table_args__ = (
        Index('m_assigrad_assuseatt_uix', 'assignment', 'userid', 'attemptnumber', unique=True),
        {'comment': 'Grading information about a single assignment submission.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    grader = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    grade = Column(DECIMAL(10, 5), server_default=text("'0.00000'"))
    attemptnumber = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MAssignOverride(Base):
    __tablename__ = 'm_assign_overrides'
    __table_args__ = {'comment': 'The overrides to assign settings.'}

    id = Column(BIGINT(10), primary_key=True)
    assignid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), index=True)
    userid = Column(BIGINT(10), index=True)
    sortorder = Column(BIGINT(10))
    allowsubmissionsfromdate = Column(BIGINT(10))
    duedate = Column(BIGINT(10))
    cutoffdate = Column(BIGINT(10))


class MAssignPluginConfig(Base):
    __tablename__ = 'm_assign_plugin_config'
    __table_args__ = {'comment': 'Config data for an instance of a plugin in an assignment.'}

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    plugin = Column(String(28, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    subtype = Column(String(28, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    name = Column(String(28, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    value = Column(LONGTEXT)


class MAssignSubmission(Base):
    __tablename__ = 'm_assign_submission'
    __table_args__ = (
        Index('m_assisubm_assusegrolat_ix', 'assignment', 'userid', 'groupid', 'latest'),
        Index('m_assisubm_assusegroatt_uix', 'assignment', 'userid', 'groupid', 'attemptnumber', unique=True),
        {'comment': 'This table keeps information about student interactions with'}
    )

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    status = Column(String(10, 'utf8mb4_bin'))
    groupid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    attemptnumber = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    latest = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MAssignUserFlag(Base):
    __tablename__ = 'm_assign_user_flags'
    __table_args__ = {'comment': 'List of flags that can be set for a single user in a single '}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    locked = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    mailed = Column(SMALLINT(4), nullable=False, index=True, server_default=text("'0'"))
    extensionduedate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    workflowstate = Column(String(20, 'utf8mb4_bin'))
    allocatedmarker = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssignUserMapping(Base):
    __tablename__ = 'm_assign_user_mapping'
    __table_args__ = {'comment': 'Map an assignment specific id number to a user'}

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MAssignfeedbackComment(Base):
    __tablename__ = 'm_assignfeedback_comments'
    __table_args__ = {'comment': 'Text feedback for submitted assignments'}

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    grade = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    commenttext = Column(LONGTEXT)
    commentformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))


class MAssignfeedbackEditpdfAnnot(Base):
    __tablename__ = 'm_assignfeedback_editpdf_annot'
    __table_args__ = (
        Index('m_assieditanno_grapag_ix', 'gradeid', 'pageno'),
        {'comment': 'stores annotations added to pdfs submitted by students'}
    )

    id = Column(BIGINT(10), primary_key=True)
    gradeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    pageno = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    x = Column(BIGINT(10), server_default=text("'0'"))
    y = Column(BIGINT(10), server_default=text("'0'"))
    endx = Column(BIGINT(10), server_default=text("'0'"))
    endy = Column(BIGINT(10), server_default=text("'0'"))
    path = Column(LONGTEXT)
    type = Column(String(10, 'utf8mb4_bin'), server_default=text("'line'"))
    colour = Column(String(10, 'utf8mb4_bin'), server_default=text("'black'"))
    draft = Column(TINYINT(2), nullable=False, server_default=text("'1'"))


class MAssignfeedbackEditpdfCmnt(Base):
    __tablename__ = 'm_assignfeedback_editpdf_cmnt'
    __table_args__ = (
        Index('m_assieditcmnt_grapag_ix', 'gradeid', 'pageno'),
        {'comment': 'Stores comments added to pdfs'}
    )

    id = Column(BIGINT(10), primary_key=True)
    gradeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    x = Column(BIGINT(10), server_default=text("'0'"))
    y = Column(BIGINT(10), server_default=text("'0'"))
    width = Column(BIGINT(10), server_default=text("'120'"))
    rawtext = Column(LONGTEXT)
    pageno = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    colour = Column(String(10, 'utf8mb4_bin'), server_default=text("'black'"))
    draft = Column(TINYINT(2), nullable=False, server_default=text("'1'"))


class MAssignfeedbackEditpdfQueue(Base):
    __tablename__ = 'm_assignfeedback_editpdf_queue'
    __table_args__ = (
        Index('m_assieditqueu_subsub_uix', 'submissionid', 'submissionattempt', unique=True),
        {'comment': 'Queue for processing.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    submissionid = Column(BIGINT(10), nullable=False)
    submissionattempt = Column(BIGINT(10), nullable=False)
    attemptedconversions = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssignfeedbackEditpdfQuick(Base):
    __tablename__ = 'm_assignfeedback_editpdf_quick'
    __table_args__ = {'comment': 'Stores teacher specified quicklist comments'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    rawtext = Column(LONGTEXT, nullable=False)
    width = Column(BIGINT(10), nullable=False, server_default=text("'120'"))
    colour = Column(String(10, 'utf8mb4_bin'), server_default=text("'yellow'"))


class MAssignfeedbackEditpdfRot(Base):
    __tablename__ = 'm_assignfeedback_editpdf_rot'
    __table_args__ = (
        Index('m_assieditrot_grapag_uix', 'gradeid', 'pageno', unique=True),
        {'comment': 'Stores rotation information of a page.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    gradeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    pageno = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    pathnamehash = Column(LONGTEXT, nullable=False)
    isrotated = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    degree = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssignfeedbackFile(Base):
    __tablename__ = 'm_assignfeedback_file'
    __table_args__ = {'comment': 'Stores info about the number of files submitted by a student'}

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    grade = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    numfiles = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssignment(Base):
    __tablename__ = 'm_assignment'
    __table_args__ = {'comment': 'Defines assignments'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    assignmenttype = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    resubmit = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    preventlate = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    emailteachers = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    var1 = Column(BIGINT(10), server_default=text("'0'"))
    var2 = Column(BIGINT(10), server_default=text("'0'"))
    var3 = Column(BIGINT(10), server_default=text("'0'"))
    var4 = Column(BIGINT(10), server_default=text("'0'"))
    var5 = Column(BIGINT(10), server_default=text("'0'"))
    maxbytes = Column(BIGINT(10), nullable=False, server_default=text("'100000'"))
    timedue = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeavailable = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    grade = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssignmentSubmission(Base):
    __tablename__ = 'm_assignment_submissions'
    __table_args__ = {'comment': 'Info about submitted assignments'}

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    numfiles = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    data1 = Column(LONGTEXT)
    data2 = Column(LONGTEXT)
    grade = Column(BIGINT(11), nullable=False, server_default=text("'0'"))
    submissioncomment = Column(LONGTEXT, nullable=False)
    format = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    teacher = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemarked = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    mailed = Column(TINYINT(1), nullable=False, index=True, server_default=text("'0'"))


class MAssignmentUpgrade(Base):
    __tablename__ = 'm_assignment_upgrade'
    __table_args__ = {'comment': 'Info about upgraded assignments'}

    id = Column(BIGINT(10), primary_key=True)
    oldcmid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    oldinstance = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    newcmid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    newinstance = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssignsubmissionFile(Base):
    __tablename__ = 'm_assignsubmission_file'
    __table_args__ = {'comment': 'Info about file submissions for assignments'}

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    submission = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    numfiles = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MAssignsubmissionOnlinetext(Base):
    __tablename__ = 'm_assignsubmission_onlinetext'
    __table_args__ = {'comment': 'Info about onlinetext submission'}

    id = Column(BIGINT(10), primary_key=True)
    assignment = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    submission = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    onlinetext = Column(LONGTEXT)
    onlineformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))


class MAuthOauth2LinkedLogin(Base):
    __tablename__ = 'm_auth_oauth2_linked_login'
    __table_args__ = (
        Index('m_authoautlinklogi_useissu_uix', 'userid', 'issuerid', 'username', unique=True),
        Index('m_authoautlinklogi_issuse_ix', 'issuerid', 'username'),
        {'comment': 'Accounts linked to a users Moodle account.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    issuerid = Column(BIGINT(10), nullable=False, index=True)
    username = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    email = Column(LONGTEXT, nullable=False)
    confirmtoken = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    confirmtokenexpires = Column(BIGINT(10))


class MBackupController(Base):
    __tablename__ = 'm_backup_controllers'
    __table_args__ = (
        Index('m_backcont_useite_ix', 'userid', 'itemid'),
        Index('m_backcont_typite_ix', 'type', 'itemid'),
        {'comment': 'To store the backup_controllers as they are used'}
    )

    id = Column(BIGINT(10), primary_key=True)
    backupid = Column(String(32, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    operation = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'backup'"))
    type = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    format = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    interactive = Column(SMALLINT(4), nullable=False)
    purpose = Column(SMALLINT(4), nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    status = Column(SMALLINT(4), nullable=False)
    execution = Column(SMALLINT(4), nullable=False)
    executiontime = Column(BIGINT(10), nullable=False)
    checksum = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    progress = Column(DECIMAL(15, 14), nullable=False, server_default=text("'0.00000000000000'"))
    controller = Column(LONGTEXT, nullable=False)


class MBackupCourse(Base):
    __tablename__ = 'm_backup_courses'
    __table_args__ = {'comment': 'To store every course backup status'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, unique=True, server_default=text("'0'"))
    laststarttime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastendtime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    laststatus = Column(String(1, 'utf8mb4_bin'), nullable=False, server_default=text("'5'"))
    nextstarttime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MBackupLog(Base):
    __tablename__ = 'm_backup_logs'
    __table_args__ = (
        Index('m_backlogs_bacid_uix', 'backupid', 'id', unique=True),
        {'comment': 'To store all the logs from backup and restore operations (by'}
    )

    id = Column(BIGINT(10), primary_key=True)
    backupid = Column(String(32, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    loglevel = Column(SMALLINT(4), nullable=False)
    message = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)


class MBadge(Base):
    __tablename__ = 'm_badge'
    __table_args__ = {'comment': 'Defines badge'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    usercreated = Column(BIGINT(10), nullable=False, index=True)
    usermodified = Column(BIGINT(10), nullable=False, index=True)
    issuername = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    issuerurl = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    issuercontact = Column(String(255, 'utf8mb4_bin'))
    expiredate = Column(BIGINT(10))
    expireperiod = Column(BIGINT(10))
    type = Column(TINYINT(1), nullable=False, index=True, server_default=text("'1'"))
    courseid = Column(BIGINT(10), index=True)
    message = Column(LONGTEXT, nullable=False)
    messagesubject = Column(LONGTEXT, nullable=False)
    attachment = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    notification = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    status = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    nextcron = Column(BIGINT(10))
    version = Column(String(255, 'utf8mb4_bin'))
    language = Column(String(255, 'utf8mb4_bin'))
    imageauthorname = Column(String(255, 'utf8mb4_bin'))
    imageauthoremail = Column(String(255, 'utf8mb4_bin'))
    imageauthorurl = Column(String(255, 'utf8mb4_bin'))
    imagecaption = Column(LONGTEXT)


class MBadgeAlignment(Base):
    __tablename__ = 'm_badge_alignment'
    __table_args__ = {'comment': 'Defines alignment for badges'}

    id = Column(BIGINT(10), primary_key=True)
    badgeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    targetname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    targeturl = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    targetdescription = Column(LONGTEXT)
    targetframework = Column(String(255, 'utf8mb4_bin'))
    targetcode = Column(String(255, 'utf8mb4_bin'))


class MBadgeBackpack(Base):
    __tablename__ = 'm_badge_backpack'
    __table_args__ = (
        Index('m_badgback_useext_uix', 'userid', 'externalbackpackid', unique=True),
        {'comment': 'Defines settings for connecting external backpack'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    email = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    backpackuid = Column(BIGINT(10), nullable=False)
    autosync = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    password = Column(String(50, 'utf8mb4_bin'))
    externalbackpackid = Column(BIGINT(10), index=True)


class MBadgeBackpackOauth2(Base):
    __tablename__ = 'm_badge_backpack_oauth2'
    __table_args__ = {'comment': 'Default comment for the table, please edit me'}

    id = Column(BIGINT(10), primary_key=True)
    usermodified = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True)
    issuerid = Column(BIGINT(10), nullable=False, index=True)
    externalbackpackid = Column(BIGINT(10), nullable=False, index=True)
    token = Column(LONGTEXT, nullable=False)
    refreshtoken = Column(LONGTEXT, nullable=False)
    expires = Column(BIGINT(10))
    scope = Column(LONGTEXT)


class MBadgeCriterion(Base):
    __tablename__ = 'm_badge_criteria'
    __table_args__ = (
        Index('m_badgcrit_badcri_uix', 'badgeid', 'criteriatype', unique=True),
        {'comment': 'Defines criteria for issuing badges'}
    )

    id = Column(BIGINT(10), primary_key=True)
    badgeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    criteriatype = Column(BIGINT(10), index=True)
    method = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MBadgeCriteriaMet(Base):
    __tablename__ = 'm_badge_criteria_met'
    __table_args__ = {'comment': 'Defines criteria that were met for an issued badge'}

    id = Column(BIGINT(10), primary_key=True)
    issuedid = Column(BIGINT(10), index=True)
    critid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    datemet = Column(BIGINT(10), nullable=False)


class MBadgeCriteriaParam(Base):
    __tablename__ = 'm_badge_criteria_param'
    __table_args__ = {'comment': 'Defines parameters for badges criteria'}

    id = Column(BIGINT(10), primary_key=True)
    critid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(String(255, 'utf8mb4_bin'))


class MBadgeEndorsement(Base):
    __tablename__ = 'm_badge_endorsement'
    __table_args__ = {'comment': 'Defines endorsement for badge'}

    id = Column(BIGINT(10), primary_key=True)
    badgeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    issuername = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    issuerurl = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    issueremail = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    claimid = Column(String(255, 'utf8mb4_bin'))
    claimcomment = Column(LONGTEXT)
    dateissued = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MBadgeExternal(Base):
    __tablename__ = 'm_badge_external'
    __table_args__ = {'comment': 'Setting for external badges display'}

    id = Column(BIGINT(10), primary_key=True)
    backpackid = Column(BIGINT(10), nullable=False, index=True)
    collectionid = Column(BIGINT(10), nullable=False)
    entityid = Column(String(255, 'utf8mb4_bin'))
    assertion = Column(LONGTEXT)


class MBadgeExternalBackpack(Base):
    __tablename__ = 'm_badge_external_backpack'
    __table_args__ = {'comment': 'Defines settings for site level backpacks that a user can co'}

    id = Column(BIGINT(10), primary_key=True)
    backpackapiurl = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    backpackweburl = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    apiversion = Column(String(12, 'utf8mb4_bin'), nullable=False, server_default=text("'1.0'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    oauth2_issuerid = Column(BIGINT(10), index=True)


class MBadgeExternalIdentifier(Base):
    __tablename__ = 'm_badge_external_identifier'
    __table_args__ = (
        Index('m_badgexteiden_sitintextty_uix', 'sitebackpackid', 'internalid', 'externalid', 'type', unique=True),
        {'comment': 'Setting for external badges mappings'}
    )

    id = Column(BIGINT(10), primary_key=True)
    sitebackpackid = Column(BIGINT(10), nullable=False, index=True)
    internalid = Column(String(128, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    externalid = Column(String(128, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    type = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MBadgeIssued(Base):
    __tablename__ = 'm_badge_issued'
    __table_args__ = (
        Index('m_badgissu_baduse_uix', 'badgeid', 'userid', unique=True),
        {'comment': 'Defines issued badges'}
    )

    id = Column(BIGINT(10), primary_key=True)
    badgeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    uniquehash = Column(LONGTEXT, nullable=False)
    dateissued = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    dateexpire = Column(BIGINT(10))
    visible = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    issuernotified = Column(BIGINT(10))


class MBadgeManualAward(Base):
    __tablename__ = 'm_badge_manual_award'
    __table_args__ = {'comment': 'Track manual award criteria for badges'}

    id = Column(BIGINT(10), primary_key=True)
    badgeid = Column(BIGINT(10), nullable=False, index=True)
    recipientid = Column(BIGINT(10), nullable=False, index=True)
    issuerid = Column(BIGINT(10), nullable=False, index=True)
    issuerrole = Column(BIGINT(10), nullable=False, index=True)
    datemet = Column(BIGINT(10), nullable=False)


class MBadgeRelated(Base):
    __tablename__ = 'm_badge_related'
    __table_args__ = (
        Index('m_badgrela_badrel_uix', 'badgeid', 'relatedbadgeid', unique=True),
        {'comment': 'Defines badge related for badges'}
    )

    id = Column(BIGINT(10), primary_key=True)
    badgeid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    relatedbadgeid = Column(BIGINT(10), index=True)


class MBlock(Base):
    __tablename__ = 'm_block'
    __table_args__ = {'comment': 'contains all installed blocks'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(40, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    cron = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastcron = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    visible = Column(TINYINT(1), nullable=False, server_default=text("'1'"))


class MBlockInstance(Base):
    __tablename__ = 'm_block_instances'
    __table_args__ = (
        Index('m_blocinst_parshopagsub_ix', 'parentcontextid', 'showinsubcontexts', 'pagetypepattern', 'subpagepattern'),
        {'comment': 'This table stores block instances. The type of block this is'}
    )

    id = Column(BIGINT(10), primary_key=True)
    blockname = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    parentcontextid = Column(BIGINT(10), nullable=False, index=True)
    showinsubcontexts = Column(SMALLINT(4), nullable=False)
    requiredbytheme = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    pagetypepattern = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    subpagepattern = Column(String(16, 'utf8mb4_bin'))
    defaultregion = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    defaultweight = Column(BIGINT(10), nullable=False)
    configdata = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False, index=True)


class MBlockPosition(Base):
    __tablename__ = 'm_block_positions'
    __table_args__ = (
        Index('m_blocposi_bloconpagsub_uix', 'blockinstanceid', 'contextid', 'pagetype', 'subpage', unique=True),
        {'comment': 'Stores the position of a sticky block_instance on a another '}
    )

    id = Column(BIGINT(10), primary_key=True)
    blockinstanceid = Column(BIGINT(10), nullable=False, index=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    pagetype = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    subpage = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    visible = Column(SMALLINT(4), nullable=False)
    region = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    weight = Column(BIGINT(10), nullable=False)


class MBlockRecentActivity(Base):
    __tablename__ = 'm_block_recent_activity'
    __table_args__ = (
        Index('m_blocreceacti_coutim_ix', 'courseid', 'timecreated'),
        {'comment': 'Recent activity block'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False)
    cmid = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False)
    action = Column(TINYINT(1), nullable=False)
    modname = Column(String(20, 'utf8mb4_bin'))


class MBlockRecentlyaccesseditem(Base):
    __tablename__ = 'm_block_recentlyaccesseditems'
    __table_args__ = (
        Index('m_blocrece_usecoucmi_uix', 'userid', 'courseid', 'cmid', unique=True),
        {'comment': 'Most recently accessed items accessed by a user'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    cmid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    timeaccess = Column(BIGINT(10), nullable=False)


class MBlockRssClient(Base):
    __tablename__ = 'm_block_rss_client'
    __table_args__ = {'comment': 'Remote news feed information. Contains the news feed id, the'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    title = Column(LONGTEXT, nullable=False)
    preferredtitle = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT, nullable=False)
    shared = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    url = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    skiptime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    skipuntil = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MBlogAssociation(Base):
    __tablename__ = 'm_blog_association'
    __table_args__ = {'comment': 'Associations of blog entries with courses and module instanc'}

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    blogid = Column(BIGINT(10), nullable=False, index=True)


class MBlogExternal(Base):
    __tablename__ = 'm_blog_external'
    __table_args__ = {'comment': 'External blog links used for RSS copying of blog entries to '}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    url = Column(LONGTEXT, nullable=False)
    filtertags = Column(String(255, 'utf8mb4_bin'))
    failedlastsync = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10))
    timefetched = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MBook(Base):
    __tablename__ = 'm_book'
    __table_args__ = {'comment': 'Defines book'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    numbering = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    navstyle = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    customtitles = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    revision = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MBookChapter(Base):
    __tablename__ = 'm_book_chapters'
    __table_args__ = {'comment': 'Defines book_chapters'}

    id = Column(BIGINT(10), primary_key=True)
    bookid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    pagenum = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    subchapter = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    title = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    content = Column(LONGTEXT, nullable=False)
    contentformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    hidden = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    importsrc = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MCacheFilter(Base):
    __tablename__ = 'm_cache_filters'
    __table_args__ = (
        Index('m_cachfilt_filmd5_ix', 'filter', 'md5key'),
        {'comment': 'For keeping information about cached data'}
    )

    id = Column(BIGINT(10), primary_key=True)
    filter = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    version = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    md5key = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    rawtext = Column(LONGTEXT, nullable=False)
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MCacheFlag(Base):
    __tablename__ = 'm_cache_flags'
    __table_args__ = {'comment': 'Cache of time-sensitive flags'}

    id = Column(BIGINT(10), primary_key=True)
    flagtype = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    value = Column(LONGTEXT, nullable=False)
    expiry = Column(BIGINT(10), nullable=False)


class MCapability(Base):
    __tablename__ = 'm_capabilities'
    __table_args__ = {'comment': 'this defines all capabilities'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    captype = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contextlevel = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    riskbitmask = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MChat(Base):
    __tablename__ = 'm_chat'
    __table_args__ = {'comment': 'Each of these is a chat room'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    keepdays = Column(BIGINT(11), nullable=False, server_default=text("'0'"))
    studentlogs = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    chattime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    schedule = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MChatMessage(Base):
    __tablename__ = 'm_chat_messages'
    __table_args__ = (
        Index('m_chatmess_timcha_ix', 'timestamp', 'chatid'),
        {'comment': 'Stores all the actual chat messages'}
    )

    id = Column(BIGINT(10), primary_key=True)
    chatid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    issystem = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    message = Column(LONGTEXT, nullable=False)
    timestamp = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MChatMessagesCurrent(Base):
    __tablename__ = 'm_chat_messages_current'
    __table_args__ = (
        Index('m_chatmesscurr_timcha_ix', 'timestamp', 'chatid'),
        {'comment': 'Stores current session'}
    )

    id = Column(BIGINT(10), primary_key=True)
    chatid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    issystem = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    message = Column(LONGTEXT, nullable=False)
    timestamp = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MChatUser(Base):
    __tablename__ = 'm_chat_users'
    __table_args__ = {'comment': 'Keeps track of which users are in which chat rooms'}

    id = Column(BIGINT(10), primary_key=True)
    chatid = Column(BIGINT(11), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(11), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(11), nullable=False, index=True, server_default=text("'0'"))
    version = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    ip = Column(String(45, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    firstping = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastping = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    lastmessageping = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    sid = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lang = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MChoice(Base):
    __tablename__ = 'm_choice'
    __table_args__ = {'comment': 'Available choices are stored here'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    publish = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    showresults = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    display = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    allowupdate = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    allowmultiple = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    showunanswered = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    includeinactive = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    limitanswers = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    timeopen = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeclose = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    showpreview = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    completionsubmit = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    showavailable = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MChoiceAnswer(Base):
    __tablename__ = 'm_choice_answers'
    __table_args__ = {'comment': 'choices performed by users'}

    id = Column(BIGINT(10), primary_key=True)
    choiceid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    optionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MChoiceOption(Base):
    __tablename__ = 'm_choice_options'
    __table_args__ = {'comment': 'available options to choice'}

    id = Column(BIGINT(10), primary_key=True)
    choiceid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    text = Column(LONGTEXT)
    maxanswers = Column(BIGINT(10)) #, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False) # server_default=text("'0'"))


class MCohort(Base):
    __tablename__ = 'm_cohort'
    __table_args__ = {'comment': 'Each record represents one cohort (aka site-wide group).'}

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    idnumber = Column(String(100, 'utf8mb4_bin'))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False)
    visible = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    theme = Column(String(50, 'utf8mb4_bin'))


class MCohortMember(Base):
    __tablename__ = 'm_cohort_members'
    __table_args__ = (
        Index('m_cohomemb_cohuse_uix', 'cohortid', 'userid', unique=True),
        {'comment': 'Link a user to a cohort.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    cohortid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeadded = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MComment(Base):
    __tablename__ = 'm_comments'
    __table_args__ = (
        Index('m_comm_concomite_ix', 'contextid', 'commentarea', 'itemid'),
        {'comment': 'moodle comments module'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False)
    component = Column(String(255, 'utf8mb4_bin'))
    commentarea = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    content = Column(LONGTEXT, nullable=False)
    format = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)


class MCompetency(Base):
    __tablename__ = 'm_competency'
    __table_args__ = (
        Index('m_comp_comidn_uix', 'competencyframeworkid', 'idnumber', unique=True),
        {'comment': 'This table contains the master record of each competency in '}
    )

    id = Column(BIGINT(10), primary_key=True)
    shortname = Column(String(100, 'utf8mb4_bin'))
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    idnumber = Column(String(100, 'utf8mb4_bin'))
    competencyframeworkid = Column(BIGINT(10), nullable=False)
    parentid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    path = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sortorder = Column(BIGINT(10), nullable=False)
    ruletype = Column(String(100, 'utf8mb4_bin'))
    ruleoutcome = Column(TINYINT(2), nullable=False, index=True, server_default=text("'0'"))
    ruleconfig = Column(LONGTEXT)
    scaleid = Column(BIGINT(10))
    scaleconfiguration = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10))


class MCompetencyCoursecomp(Base):
    __tablename__ = 'm_competency_coursecomp'
    __table_args__ = (
        Index('m_compcour_courul_ix', 'courseid', 'ruleoutcome'),
        Index('m_compcour_coucom_uix', 'courseid', 'competencyid', unique=True),
        {'comment': 'Link a competency to a course.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    competencyid = Column(BIGINT(10), nullable=False, index=True)
    ruleoutcome = Column(TINYINT(2), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    sortorder = Column(BIGINT(10), nullable=False)


class MCompetencyCoursecompsetting(Base):
    __tablename__ = 'm_competency_coursecompsetting'
    __table_args__ = {'comment': 'This table contains the course specific settings for compete'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, unique=True)
    pushratingstouserplans = Column(TINYINT(2))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10))


class MCompetencyEvidence(Base):
    __tablename__ = 'm_competency_evidence'
    __table_args__ = {'comment': 'The evidence linked to a user competency'}

    id = Column(BIGINT(10), primary_key=True)
    usercompetencyid = Column(BIGINT(10), nullable=False, index=True)
    contextid = Column(BIGINT(10), nullable=False)
    action = Column(TINYINT(2), nullable=False)
    actionuserid = Column(BIGINT(10))
    descidentifier = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    desccomponent = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    desca = Column(LONGTEXT)
    url = Column(String(255, 'utf8mb4_bin'))
    grade = Column(BIGINT(10))
    note = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyFramework(Base):
    __tablename__ = 'm_competency_framework'
    __table_args__ = {'comment': 'List of competency frameworks.'}

    id = Column(BIGINT(10), primary_key=True)
    shortname = Column(String(100, 'utf8mb4_bin'))
    contextid = Column(BIGINT(10), nullable=False)
    idnumber = Column(String(100, 'utf8mb4_bin'), unique=True)
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    scaleid = Column(BIGINT(11))
    scaleconfiguration = Column(LONGTEXT, nullable=False)
    visible = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    taxonomies = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10))


class MCompetencyModulecomp(Base):
    __tablename__ = 'm_competency_modulecomp'
    __table_args__ = (
        Index('m_compmodu_cmicom_uix', 'cmid', 'competencyid', unique=True),
        Index('m_compmodu_cmirul_ix', 'cmid', 'ruleoutcome'),
        {'comment': 'Link a competency to a module.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    cmid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    sortorder = Column(BIGINT(10), nullable=False)
    competencyid = Column(BIGINT(10), nullable=False, index=True)
    ruleoutcome = Column(TINYINT(2), nullable=False)


class MCompetencyPlan(Base):
    __tablename__ = 'm_competency_plan'
    __table_args__ = (
        Index('m_compplan_usesta_ix', 'userid', 'status'),
        Index('m_compplan_stadue_ix', 'status', 'duedate'),
        {'comment': 'Learning plans'}
    )

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False)
    templateid = Column(BIGINT(10), index=True)
    origtemplateid = Column(BIGINT(10))
    status = Column(TINYINT(1), nullable=False)
    duedate = Column(BIGINT(10), server_default=text("'0'"))
    reviewerid = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyPlancomp(Base):
    __tablename__ = 'm_competency_plancomp'
    __table_args__ = (
        Index('m_compplan_placom_uix', 'planid', 'competencyid', unique=True),
        {'comment': 'Plan competencies'}
    )

    id = Column(BIGINT(10), primary_key=True)
    planid = Column(BIGINT(10), nullable=False)
    competencyid = Column(BIGINT(10), nullable=False)
    sortorder = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10))
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyRelatedcomp(Base):
    __tablename__ = 'm_competency_relatedcomp'
    __table_args__ = {'comment': 'Related competencies'}

    id = Column(BIGINT(10), primary_key=True)
    competencyid = Column(BIGINT(10), nullable=False)
    relatedcompetencyid = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10))
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyTemplate(Base):
    __tablename__ = 'm_competency_template'
    __table_args__ = {'comment': 'Learning plan templates.'}

    id = Column(BIGINT(10), primary_key=True)
    shortname = Column(String(100, 'utf8mb4_bin'))
    contextid = Column(BIGINT(10), nullable=False)
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    visible = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    duedate = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10))


class MCompetencyTemplatecohort(Base):
    __tablename__ = 'm_competency_templatecohort'
    __table_args__ = (
        Index('m_comptemp_temcoh_uix', 'templateid', 'cohortid', unique=True),
        {'comment': 'Default comment for the table, please edit me'}
    )

    id = Column(BIGINT(10), primary_key=True)
    templateid = Column(BIGINT(10), nullable=False, index=True)
    cohortid = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyTemplatecomp(Base):
    __tablename__ = 'm_competency_templatecomp'
    __table_args__ = {'comment': 'Link a competency to a learning plan template.'}

    id = Column(BIGINT(10), primary_key=True)
    templateid = Column(BIGINT(10), nullable=False, index=True)
    competencyid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    sortorder = Column(BIGINT(10))


class MCompetencyUsercomp(Base):
    __tablename__ = 'm_competency_usercomp'
    __table_args__ = (
        Index('m_compuser_usecom_uix', 'userid', 'competencyid', unique=True),
        {'comment': 'User competencies'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False)
    competencyid = Column(BIGINT(10), nullable=False)
    status = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    reviewerid = Column(BIGINT(10))
    proficiency = Column(TINYINT(2))
    grade = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10))
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyUsercompcourse(Base):
    __tablename__ = 'm_competency_usercompcourse'
    __table_args__ = (
        Index('m_compuser_usecoucom_uix', 'userid', 'courseid', 'competencyid', unique=True),
        {'comment': 'User competencies in a course'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False)
    courseid = Column(BIGINT(10), nullable=False)
    competencyid = Column(BIGINT(10), nullable=False)
    proficiency = Column(TINYINT(2))
    grade = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10))
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyUsercompplan(Base):
    __tablename__ = 'm_competency_usercompplan'
    __table_args__ = (
        Index('m_compuser_usecompla_uix', 'userid', 'competencyid', 'planid', unique=True),
        {'comment': 'User competencies plans'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False)
    competencyid = Column(BIGINT(10), nullable=False)
    planid = Column(BIGINT(10), nullable=False)
    proficiency = Column(TINYINT(2))
    grade = Column(BIGINT(10))
    sortorder = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10))
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyUserevidence(Base):
    __tablename__ = 'm_competency_userevidence'
    __table_args__ = {'comment': 'The evidence of prior learning'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT, nullable=False)
    descriptionformat = Column(TINYINT(1), nullable=False)
    url = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)


class MCompetencyUserevidencecomp(Base):
    __tablename__ = 'm_competency_userevidencecomp'
    __table_args__ = (
        Index('m_compuser_usecom2_uix', 'userevidenceid', 'competencyid', unique=True),
        {'comment': 'Relationship between user evidence and competencies'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userevidenceid = Column(BIGINT(10), nullable=False, index=True)
    competencyid = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)


class MConfig(Base):
    __tablename__ = 'm_config'
    __table_args__ = {'comment': 'Moodle configuration variables'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    value = Column(LONGTEXT, nullable=False)


class MConfigLog(Base):
    __tablename__ = 'm_config_log'
    __table_args__ = {'comment': 'Changes done in server configuration through admin UI'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    timemodified = Column(BIGINT(10), nullable=False, index=True)
    plugin = Column(String(100, 'utf8mb4_bin'))
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT)
    oldvalue = Column(LONGTEXT)


class MConfigPlugin(Base):
    __tablename__ = 'm_config_plugins'
    __table_args__ = (
        Index('m_confplug_plunam_uix', 'plugin', 'name', unique=True),
        {'comment': 'Moodle modules and plugins configuration variables'}
    )

    id = Column(BIGINT(10), primary_key=True)
    plugin = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("'core'"))
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT, nullable=False)


class MContentbankContent(Base):
    __tablename__ = 'm_contentbank_content'
    __table_args__ = (
        Index('m_contcont_conconins_ix', 'contextid', 'contenttype', 'instanceid'),
        {'comment': 'This table stores content data in the content bank.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    contenttype = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contextid = Column(BIGINT(10), nullable=False, index=True)
    visibility = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    instanceid = Column(BIGINT(10))
    configdata = Column(LONGTEXT)
    usercreated = Column(BIGINT(10), nullable=False, index=True)
    usermodified = Column(BIGINT(10), index=True)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), server_default=text("'0'"))


class MContext(Base):
    __tablename__ = 'm_context'
    __table_args__ = (
        Index('m_cont_conins_uix', 'contextlevel', 'instanceid', unique=True),
        {'comment': 'one of these must be set'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextlevel = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    instanceid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    path = Column(String(255, 'utf8mb4_bin'), index=True)
    depth = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    locked = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MContextTemp(Base):
    __tablename__ = 'm_context_temp'
    __table_args__ = {'comment': 'Used by build_context_path() in upgrade and cron to keep con'}

    id = Column(BIGINT(10), primary_key=True)
    path = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    depth = Column(TINYINT(2), nullable=False)
    locked = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MCourse(Base):
    __tablename__ = 'm_course'
    __table_args__ = {'comment': 'Central course table'}

    id = Column(BIGINT(10), primary_key=True)
    category = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    sortorder = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    fullname = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    idnumber = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    summary = Column(LONGTEXT)
    summaryformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    format = Column(String(21, 'utf8mb4_bin'), nullable=False, server_default=text("'topics'"))
    showgrades = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    newsitems = Column(MEDIUMINT(5), nullable=False, server_default=text("'1'"))
    startdate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    enddate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    relativedatesmode = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    marker = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    maxbytes = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    legacyfiles = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    showreports = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    visible = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    visibleold = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    downloadcontent = Column(TINYINT(1))
    groupmode = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    groupmodeforce = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    defaultgroupingid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lang = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    calendartype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    theme = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    requested = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    enablecompletion = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    completionnotify = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    cacherev = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    originalcourseid = Column(BIGINT(10))
    showactivitydates = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    showcompletionconditions = Column(TINYINT(1))


class MCourseCategory(Base):
    __tablename__ = 'm_course_categories'
    __table_args__ = {'comment': 'Course categories'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    idnumber = Column(String(100, 'utf8mb4_bin'))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    parent = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    coursecount = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    visible = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    visibleold = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    depth = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    path = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    theme = Column(String(50, 'utf8mb4_bin'))


class MCourseCompletionAggrMethd(Base):
    __tablename__ = 'm_course_completion_aggr_methd'
    __table_args__ = (
        Index('m_courcompaggrmeth_coucri_uix', 'course', 'criteriatype', unique=True),
        {'comment': 'Course completion aggregation methods for criteria'}
    )

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    criteriatype = Column(BIGINT(10), index=True)
    method = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    value = Column(DECIMAL(10, 5))


class MCourseCompletionCritCompl(Base):
    __tablename__ = 'm_course_completion_crit_compl'
    __table_args__ = (
        Index('m_courcompcritcomp_usecouc_uix', 'userid', 'course', 'criteriaid', unique=True),
        {'comment': 'Course completion user records'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    criteriaid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    gradefinal = Column(DECIMAL(10, 5))
    unenroled = Column(BIGINT(10))
    timecompleted = Column(BIGINT(10), index=True)


class MCourseCompletionCriterion(Base):
    __tablename__ = 'm_course_completion_criteria'
    __table_args__ = {'comment': 'Course completion criteria'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    criteriatype = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    module = Column(String(100, 'utf8mb4_bin'))
    moduleinstance = Column(BIGINT(10))
    courseinstance = Column(BIGINT(10))
    enrolperiod = Column(BIGINT(10))
    timeend = Column(BIGINT(10))
    gradepass = Column(DECIMAL(10, 5))
    role = Column(BIGINT(10))


class MCourseCompletionDefault(Base):
    __tablename__ = 'm_course_completion_defaults'
    __table_args__ = (
        Index('m_courcompdefa_coumod_uix', 'course', 'module', unique=True),
        {'comment': 'Default settings for activities completion'}
    )

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True)
    module = Column(BIGINT(10), nullable=False, index=True)
    completion = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    completionview = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    completionusegrade = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    completionexpected = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    customrules = Column(LONGTEXT)


class MCourseCompletion(Base):
    __tablename__ = 'm_course_completions'
    __table_args__ = (
        Index('m_courcomp_usecou_uix', 'userid', 'course', unique=True),
        {'comment': 'Course completion records'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeenrolled = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timestarted = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timecompleted = Column(BIGINT(10), index=True)
    reaggregate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MCourseFormatOption(Base):
    __tablename__ = 'm_course_format_options'
    __table_args__ = (
        Index('m_courformopti_couforsecna_uix', 'courseid', 'format', 'sectionid', 'name', unique=True),
        {'comment': 'Stores format-specific options for the course or course sect'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    format = Column(String(21, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sectionid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT)


class MCourseModule(Base):
    __tablename__ = 'm_course_modules'
    __table_args__ = (
        Index('m_courmodu_idncou_ix', 'idnumber', 'course'),
        {'comment': 'course_modules table retrofitted from MySQL'}
    )

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    module = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    instance = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    section = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    idnumber = Column(String(100, 'utf8mb4_bin'))
    added = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    score = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    indent = Column(MEDIUMINT(5), nullable=False, server_default=text("'0'"))
    visible = Column(TINYINT(1), nullable=False, index=True, server_default=text("'1'"))
    visibleoncoursepage = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    visibleold = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    groupmode = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    groupingid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    completion = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    completiongradeitemnumber = Column(BIGINT(10))
    completionview = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    completionexpected = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    showdescription = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    availability = Column(LONGTEXT)
    deletioninprogress = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MCourseModulesCompletion(Base):
    __tablename__ = 'm_course_modules_completion'
    __table_args__ = (
        Index('m_courmoducomp_usecou_uix', 'userid', 'coursemoduleid', unique=True),
        {'comment': 'Stores the completion state (completed or not completed, etc'}
    )

    id = Column(BIGINT(10), primary_key=True)
    coursemoduleid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False)
    completionstate = Column(TINYINT(1), nullable=False)
    viewed = Column(TINYINT(1))
    overrideby = Column(BIGINT(10))
    timemodified = Column(BIGINT(10), nullable=False)


class MCoursePublished(Base):
    __tablename__ = 'm_course_published'
    __table_args__ = {'comment': 'Information about how and when an local courses were publish'}

    id = Column(BIGINT(10), primary_key=True)
    huburl = Column(String(255, 'utf8mb4_bin'))
    courseid = Column(BIGINT(10), nullable=False)
    timepublished = Column(BIGINT(10), nullable=False)
    enrollable = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    hubcourseid = Column(BIGINT(10), nullable=False)
    status = Column(TINYINT(1), server_default=text("'0'"))
    timechecked = Column(BIGINT(10))


class MCourseRequest(Base):
    __tablename__ = 'm_course_request'
    __table_args__ = {'comment': 'course requests'}

    id = Column(BIGINT(10), primary_key=True)
    fullname = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    shortname = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    summary = Column(LONGTEXT, nullable=False)
    summaryformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    category = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    reason = Column(LONGTEXT, nullable=False)
    requester = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    password = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MCourseSection(Base):
    __tablename__ = 'm_course_sections'
    __table_args__ = (
        Index('m_coursect_cousec_uix', 'course', 'section', unique=True),
        {'comment': 'to define the sections for each course'}
    )

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    section = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'))
    summary = Column(LONGTEXT)
    summaryformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    sequence = Column(LONGTEXT)
    visible = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    availability = Column(LONGTEXT)
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MCustomfieldCategory(Base):
    __tablename__ = 'm_customfield_category'
    __table_args__ = (
        Index('m_custcate_comareitesor_ix', 'component', 'area', 'itemid', 'sortorder'),
        {'comment': 'core_customfield category table'}
    )

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(400, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(BIGINT(10))
    sortorder = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    area = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    contextid = Column(BIGINT(10), index=True)


class MCustomfieldDatum(Base):
    __tablename__ = 'm_customfield_data'
    __table_args__ = (
        Index('m_custdata_fieint_ix', 'fieldid', 'intvalue'),
        Index('m_custdata_fiesho_ix', 'fieldid', 'shortcharvalue'),
        Index('m_custdata_insfie_uix', 'instanceid', 'fieldid', unique=True),
        Index('m_custdata_fiedec_ix', 'fieldid', 'decvalue'),
        {'comment': 'core_customfield data table'}
    )

    id = Column(BIGINT(10), primary_key=True)
    fieldid = Column(BIGINT(10), nullable=False, index=True)
    instanceid = Column(BIGINT(10), nullable=False)
    intvalue = Column(BIGINT(10))
    decvalue = Column(DECIMAL(10, 5))
    shortcharvalue = Column(String(255, 'utf8mb4_bin'))
    charvalue = Column(String(1333, 'utf8mb4_bin'))
    value = Column(LONGTEXT, nullable=False)
    valueformat = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    contextid = Column(BIGINT(10), index=True)


class MCustomfieldField(Base):
    __tablename__ = 'm_customfield_field'
    __table_args__ = (
        Index('m_custfiel_catsor_ix', 'categoryid', 'sortorder'),
        {'comment': 'core_customfield field table'}
    )

    id = Column(BIGINT(10), primary_key=True)
    shortname = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    name = Column(String(400, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    type = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(BIGINT(10))
    sortorder = Column(BIGINT(10))
    categoryid = Column(BIGINT(10), index=True)
    configdata = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MDatum(Base):
    __tablename__ = 'm_data'
    __table_args__ = {'comment': 'all database activities'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    comments = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    timeavailablefrom = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeavailableto = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeviewfrom = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeviewto = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    requiredentries = Column(INTEGER(8), nullable=False, server_default=text("'0'"))
    requiredentriestoview = Column(INTEGER(8), nullable=False, server_default=text("'0'"))
    maxentries = Column(INTEGER(8), nullable=False, server_default=text("'0'"))
    rssarticles = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    singletemplate = Column(LONGTEXT)
    listtemplate = Column(LONGTEXT)
    listtemplateheader = Column(LONGTEXT)
    listtemplatefooter = Column(LONGTEXT)
    addtemplate = Column(LONGTEXT)
    rsstemplate = Column(LONGTEXT)
    rsstitletemplate = Column(LONGTEXT)
    csstemplate = Column(LONGTEXT)
    jstemplate = Column(LONGTEXT)
    asearchtemplate = Column(LONGTEXT)
    approval = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    manageapproved = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    scale = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assessed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assesstimestart = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assesstimefinish = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    defaultsort = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    defaultsortdir = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    editany = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    notification = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    config = Column(LONGTEXT)
    completionentries = Column(BIGINT(10), server_default=text("'0'"))


class MDataContent(Base):
    __tablename__ = 'm_data_content'
    __table_args__ = {'comment': 'the content introduced in each record/fields'}

    id = Column(BIGINT(10), primary_key=True)
    fieldid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    recordid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    content = Column(LONGTEXT)
    content1 = Column(LONGTEXT)
    content2 = Column(LONGTEXT)
    content3 = Column(LONGTEXT)
    content4 = Column(LONGTEXT)


class MDataField(Base):
    __tablename__ = 'm_data_fields'
    __table_args__ = (
        Index('m_datafiel_typdat_ix', 'type', 'dataid'),
        {'comment': 'every field available'}
    )

    id = Column(BIGINT(10), primary_key=True)
    dataid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    type = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT, nullable=False)
    required = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    param1 = Column(LONGTEXT)
    param2 = Column(LONGTEXT)
    param3 = Column(LONGTEXT)
    param4 = Column(LONGTEXT)
    param5 = Column(LONGTEXT)
    param6 = Column(LONGTEXT)
    param7 = Column(LONGTEXT)
    param8 = Column(LONGTEXT)
    param9 = Column(LONGTEXT)
    param10 = Column(LONGTEXT)


class MDataRecord(Base):
    __tablename__ = 'm_data_records'
    __table_args__ = {'comment': 'every record introduced'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    dataid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    approved = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))


class MEditorAttoAutosave(Base):
    __tablename__ = 'm_editor_atto_autosave'
    __table_args__ = (
        Index('m_editattoauto_eleconusepa_uix', 'elementid', 'contextid', 'userid', 'pagehash', unique=True),
        {'comment': 'Draft text that is auto-saved every 5 seconds while an edito'}
    )

    id = Column(BIGINT(10), primary_key=True)
    elementid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contextid = Column(BIGINT(10), nullable=False)
    pagehash = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    userid = Column(BIGINT(10), nullable=False)
    drafttext = Column(LONGTEXT, nullable=False)
    draftid = Column(BIGINT(10))
    pageinstance = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MEnrol(Base):
    __tablename__ = 'm_enrol'
    __table_args__ = {'comment': 'Instances of enrolment plugins used in courses, fields marke'}

    id = Column(BIGINT(10), primary_key=True)
    enrol = Column(String(20, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    status = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, index=True)
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'))
    enrolperiod = Column(BIGINT(10), server_default=text("'0'"))
    enrolstartdate = Column(BIGINT(10), server_default=text("'0'"))
    enrolenddate = Column(BIGINT(10), server_default=text("'0'"))
    expirynotify = Column(TINYINT(1), server_default=text("'0'"))
    expirythreshold = Column(BIGINT(10), server_default=text("'0'"))
    notifyall = Column(TINYINT(1), server_default=text("'0'"))
    password = Column(String(50, 'utf8mb4_bin'))
    cost = Column(String(20, 'utf8mb4_bin'))
    currency = Column(String(3, 'utf8mb4_bin'))
    roleid = Column(BIGINT(10), server_default=text("'0'"))
    customint1 = Column(BIGINT(10))
    customint2 = Column(BIGINT(10))
    customint3 = Column(BIGINT(10))
    customint4 = Column(BIGINT(10))
    customint5 = Column(BIGINT(10))
    customint6 = Column(BIGINT(10))
    customint7 = Column(BIGINT(10))
    customint8 = Column(BIGINT(10))
    customchar1 = Column(String(255, 'utf8mb4_bin'))
    customchar2 = Column(String(255, 'utf8mb4_bin'))
    customchar3 = Column(String(1333, 'utf8mb4_bin'))
    customdec1 = Column(DECIMAL(12, 7))
    customdec2 = Column(DECIMAL(12, 7))
    customtext1 = Column(LONGTEXT)
    customtext2 = Column(LONGTEXT)
    customtext3 = Column(LONGTEXT)
    customtext4 = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MEnrolFlatfile(Base):
    __tablename__ = 'm_enrol_flatfile'
    __table_args__ = {'comment': 'enrol_flatfile table retrofitted from MySQL'}

    id = Column(BIGINT(10), primary_key=True)
    action = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    roleid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    timestart = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MEnrolLtiLti2Consumer(Base):
    __tablename__ = 'm_enrol_lti_lti2_consumer'
    __table_args__ = {'comment': 'LTI consumers interacting with moodle'}

    id = Column(BIGINT(11), primary_key=True)
    name = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    consumerkey256 = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    consumerkey = Column(LONGTEXT)
    secret = Column(String(1024, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    ltiversion = Column(String(10, 'utf8mb4_bin'))
    consumername = Column(String(255, 'utf8mb4_bin'))
    consumerversion = Column(String(255, 'utf8mb4_bin'))
    consumerguid = Column(String(1024, 'utf8mb4_bin'))
    profile = Column(LONGTEXT)
    toolproxy = Column(LONGTEXT)
    settings = Column(LONGTEXT)
    protected = Column(TINYINT(1), nullable=False)
    enabled = Column(TINYINT(1), nullable=False)
    enablefrom = Column(BIGINT(10))
    enableuntil = Column(BIGINT(10))
    lastaccess = Column(BIGINT(10))
    created = Column(BIGINT(10), nullable=False)
    updated = Column(BIGINT(10), nullable=False)


class MEnrolLtiLti2Context(Base):
    __tablename__ = 'm_enrol_lti_lti2_context'
    __table_args__ = {'comment': 'Information about a specific LTI contexts from the consumers'}

    id = Column(BIGINT(11), primary_key=True)
    consumerid = Column(BIGINT(11), nullable=False, index=True)
    lticontextkey = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    type = Column(String(100, 'utf8mb4_bin'))
    settings = Column(LONGTEXT)
    created = Column(BIGINT(10), nullable=False)
    updated = Column(BIGINT(10), nullable=False)


class MEnrolLtiLti2Nonce(Base):
    __tablename__ = 'm_enrol_lti_lti2_nonce'
    __table_args__ = {'comment': 'Nonce used for authentication between moodle and a consumer'}

    id = Column(BIGINT(11), primary_key=True)
    consumerid = Column(BIGINT(11), nullable=False, index=True)
    value = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    expires = Column(BIGINT(10), nullable=False)


class MEnrolLtiLti2ResourceLink(Base):
    __tablename__ = 'm_enrol_lti_lti2_resource_link'
    __table_args__ = {'comment': 'Link from the consumer to the tool'}

    id = Column(BIGINT(11), primary_key=True)
    contextid = Column(BIGINT(11), index=True)
    consumerid = Column(BIGINT(11), index=True)
    ltiresourcelinkkey = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    settings = Column(LONGTEXT)
    primaryresourcelinkid = Column(BIGINT(11), index=True)
    shareapproved = Column(TINYINT(1))
    created = Column(BIGINT(10), nullable=False)
    updated = Column(BIGINT(10), nullable=False)


class MEnrolLtiLti2ShareKey(Base):
    __tablename__ = 'm_enrol_lti_lti2_share_key'
    __table_args__ = {'comment': 'Resource link share key'}

    id = Column(BIGINT(11), primary_key=True)
    sharekey = Column(String(32, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    resourcelinkid = Column(BIGINT(11), nullable=False, unique=True)
    autoapprove = Column(TINYINT(1), nullable=False)
    expires = Column(BIGINT(10), nullable=False)


class MEnrolLtiLti2ToolProxy(Base):
    __tablename__ = 'm_enrol_lti_lti2_tool_proxy'
    __table_args__ = {'comment': 'A tool proxy between moodle and a consumer'}

    id = Column(BIGINT(11), primary_key=True)
    toolproxykey = Column(String(32, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    consumerid = Column(BIGINT(11), nullable=False, index=True)
    toolproxy = Column(LONGTEXT, nullable=False)
    created = Column(BIGINT(10), nullable=False)
    updated = Column(BIGINT(10), nullable=False)


class MEnrolLtiLti2UserResult(Base):
    __tablename__ = 'm_enrol_lti_lti2_user_result'
    __table_args__ = {'comment': 'Results for each user for each resource link'}

    id = Column(BIGINT(11), primary_key=True)
    resourcelinkid = Column(BIGINT(11), nullable=False, index=True)
    ltiuserkey = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    ltiresultsourcedid = Column(String(1024, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    created = Column(BIGINT(10), nullable=False)
    updated = Column(BIGINT(10), nullable=False)


class MEnrolLtiToolConsumerMap(Base):
    __tablename__ = 'm_enrol_lti_tool_consumer_map'
    __table_args__ = {'comment': 'Table that maps the published tool to tool consumers.'}

    id = Column(BIGINT(10), primary_key=True)
    toolid = Column(BIGINT(11), nullable=False, index=True)
    consumerid = Column(BIGINT(11), nullable=False, index=True)


class MEnrolLtiTool(Base):
    __tablename__ = 'm_enrol_lti_tools'
    __table_args__ = {'comment': 'List of tools provided to the remote system'}

    id = Column(BIGINT(10), primary_key=True)
    enrolid = Column(BIGINT(10), nullable=False, index=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    institution = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    lang = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("'en'"))
    timezone = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("'99'"))
    maxenrolled = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    maildisplay = Column(TINYINT(2), nullable=False, server_default=text("'2'"))
    city = Column(String(120, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    country = Column(String(2, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    gradesync = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    gradesynccompletion = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    membersync = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    membersyncmode = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    roleinstructor = Column(BIGINT(10), nullable=False)
    rolelearner = Column(BIGINT(10), nullable=False)
    secret = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MEnrolLtiUser(Base):
    __tablename__ = 'm_enrol_lti_users'
    __table_args__ = {'comment': 'User access log and gradeback data'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    toolid = Column(BIGINT(10), nullable=False, index=True)
    serviceurl = Column(LONGTEXT)
    sourceid = Column(LONGTEXT)
    consumerkey = Column(LONGTEXT)
    consumersecret = Column(LONGTEXT)
    membershipsurl = Column(LONGTEXT)
    membershipsid = Column(LONGTEXT)
    lastgrade = Column(DECIMAL(10, 5))
    lastaccess = Column(BIGINT(10))
    timecreated = Column(BIGINT(10))


class MEnrolPaypal(Base):
    __tablename__ = 'm_enrol_paypal'
    __table_args__ = {'comment': 'Holds all known information about PayPal transactions'}

    id = Column(BIGINT(10), primary_key=True)
    business = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    receiver_email = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    receiver_id = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    item_name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    instanceid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    memo = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    tax = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    option_name1 = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    option_selection1_x = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    option_name2 = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    option_selection2_x = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    payment_status = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    pending_reason = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    reason_code = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    txn_id = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    parent_txn_id = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    payment_type = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timeupdated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MEvent(Base):
    __tablename__ = 'm_event'
    __table_args__ = (
        Index('m_even_modinseve_ix', 'modulename', 'instance', 'eventtype'),
        Index('m_even_typtim_ix', 'type', 'timesort'),
        Index('m_even_grocoucatvisuse_ix', 'groupid', 'courseid', 'categoryid', 'visible', 'userid'),
        Index('m_even_comeveins_ix', 'component', 'eventtype', 'instance'),
        {'comment': 'For everything with a time associated to it'}
    )

    id = Column(BIGINT(10), primary_key=True)
    name = Column(LONGTEXT, nullable=False)
    description = Column(LONGTEXT, nullable=False)
    format = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    categoryid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    repeatid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    component = Column(String(100, 'utf8mb4_bin'))
    modulename = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    instance = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    type = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    eventtype = Column(String(20, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    timestart = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeduration = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timesort = Column(BIGINT(10))
    visible = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    uuid = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    sequence = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    subscriptionid = Column(BIGINT(10), index=True)
    priority = Column(BIGINT(10))
    location = Column(LONGTEXT)


class MEventSubscription(Base):
    __tablename__ = 'm_event_subscriptions'
    __table_args__ = {'comment': 'Tracks subscriptions to remote calendars.'}

    id = Column(BIGINT(10), primary_key=True)
    url = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    categoryid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    eventtype = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    pollinterval = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastupdated = Column(BIGINT(10))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MEventsHandler(Base):
    __tablename__ = 'm_events_handlers'
    __table_args__ = (
        Index('m_evenhand_evecom_uix', 'eventname', 'component', unique=True),
        {'comment': 'This table is for storing which components requests what typ'}
    )

    id = Column(BIGINT(10), primary_key=True)
    eventname = Column(String(166, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    component = Column(String(166, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    handlerfile = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    handlerfunction = Column(LONGTEXT)
    schedule = Column(String(255, 'utf8mb4_bin'))
    status = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    internal = Column(TINYINT(2), nullable=False, server_default=text("'1'"))


class MEventsQueue(Base):
    __tablename__ = 'm_events_queue'
    __table_args__ = {'comment': 'This table is for storing queued events. It stores only one '}

    id = Column(BIGINT(10), primary_key=True)
    eventdata = Column(LONGTEXT, nullable=False)
    stackdump = Column(LONGTEXT)
    userid = Column(BIGINT(10), index=True)
    timecreated = Column(BIGINT(10), nullable=False)


class MEventsQueueHandler(Base):
    __tablename__ = 'm_events_queue_handlers'
    __table_args__ = {'comment': 'This is the list of queued handlers for processing. The even'}

    id = Column(BIGINT(10), primary_key=True)
    queuedeventid = Column(BIGINT(10), nullable=False, index=True)
    handlerid = Column(BIGINT(10), nullable=False, index=True)
    status = Column(BIGINT(10))
    errormessage = Column(LONGTEXT)
    timemodified = Column(BIGINT(10), nullable=False)


class MExternalFunction(Base):
    __tablename__ = 'm_external_functions'
    __table_args__ = {'comment': 'list of all external functions'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(200, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    classname = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    methodname = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    classpath = Column(String(255, 'utf8mb4_bin'))
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    capabilities = Column(String(255, 'utf8mb4_bin'))
    services = Column(String(1333, 'utf8mb4_bin'))


class MExternalService(Base):
    __tablename__ = 'm_external_services'
    __table_args__ = {'comment': 'built in and custom external services'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(200, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    enabled = Column(TINYINT(1), nullable=False)
    requiredcapability = Column(String(150, 'utf8mb4_bin'))
    restrictedusers = Column(TINYINT(1), nullable=False)
    component = Column(String(100, 'utf8mb4_bin'))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10))
    shortname = Column(String(255, 'utf8mb4_bin'))
    downloadfiles = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    uploadfiles = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MExternalServicesFunction(Base):
    __tablename__ = 'm_external_services_functions'
    __table_args__ = {'comment': 'lists functions available in each service group'}

    id = Column(BIGINT(10), primary_key=True)
    externalserviceid = Column(BIGINT(10), nullable=False, index=True)
    functionname = Column(String(200, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MExternalServicesUser(Base):
    __tablename__ = 'm_external_services_users'
    __table_args__ = {'comment': 'users allowed to use services with restricted users flag'}

    id = Column(BIGINT(10), primary_key=True)
    externalserviceid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    iprestriction = Column(String(255, 'utf8mb4_bin'))
    validuntil = Column(BIGINT(10))
    timecreated = Column(BIGINT(10))


class MExternalToken(Base):
    __tablename__ = 'm_external_tokens'
    __table_args__ = {'comment': 'Security tokens for accessing of external services'}

    id = Column(BIGINT(10), primary_key=True)
    token = Column(String(128, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    privatetoken = Column(String(64, 'utf8mb4_bin'))
    tokentype = Column(SMALLINT(4), nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    externalserviceid = Column(BIGINT(10), nullable=False, index=True)
    sid = Column(String(128, 'utf8mb4_bin'))
    contextid = Column(BIGINT(10), nullable=False, index=True)
    creatorid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'1'"))
    iprestriction = Column(String(255, 'utf8mb4_bin'))
    validuntil = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    lastaccess = Column(BIGINT(10))


class MFavourite(Base):
    __tablename__ = 'm_favourite'
    __table_args__ = (
        Index('m_favo_comiteiteconuse_uix', 'component', 'itemtype', 'itemid', 'contextid', 'userid', unique=True),
        {'comment': 'Stores the relationship between an arbitrary item (itemtype,'}
    )

    id = Column(BIGINT(10), primary_key=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemtype = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    ordering = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MFeedback(Base):
    __tablename__ = 'm_feedback'
    __table_args__ = {'comment': 'all feedbacks'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    anonymous = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    email_notification = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    multiple_submit = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    autonumbering = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    site_after_submit = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    page_after_submit = Column(LONGTEXT, nullable=False)
    page_after_submitformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    publish_stats = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timeopen = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeclose = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    completionsubmit = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MFeedbackCompleted(Base):
    __tablename__ = 'm_feedback_completed'
    __table_args__ = {'comment': 'filled out feedback'}

    id = Column(BIGINT(10), primary_key=True)
    feedback = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    random_response = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    anonymous_response = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MFeedbackCompletedtmp(Base):
    __tablename__ = 'm_feedback_completedtmp'
    __table_args__ = {'comment': 'filled out feedback'}

    id = Column(BIGINT(10), primary_key=True)
    feedback = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    guestid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    random_response = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    anonymous_response = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MFeedbackItem(Base):
    __tablename__ = 'm_feedback_item'
    __table_args__ = {'comment': 'feedback_items'}

    id = Column(BIGINT(10), primary_key=True)
    feedback = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    template = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    label = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    presentation = Column(LONGTEXT, nullable=False)
    typ = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    hasvalue = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    position = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    required = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    dependitem = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    dependvalue = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    options = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MFeedbackSitecourseMap(Base):
    __tablename__ = 'm_feedback_sitecourse_map'
    __table_args__ = {'comment': 'feedback sitecourse map'}

    id = Column(BIGINT(10), primary_key=True)
    feedbackid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MFeedbackTemplate(Base):
    __tablename__ = 'm_feedback_template'
    __table_args__ = {'comment': 'templates of feedbackstructures'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    ispublic = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MFeedbackValue(Base):
    __tablename__ = 'm_feedback_value'
    __table_args__ = (
        Index('m_feedvalu_comitecou_uix', 'completed', 'item', 'course_id', unique=True),
        {'comment': 'values of the completeds'}
    )

    id = Column(BIGINT(10), primary_key=True)
    course_id = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    item = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    completed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    tmp_completed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    value = Column(LONGTEXT, nullable=False)


class MFeedbackValuetmp(Base):
    __tablename__ = 'm_feedback_valuetmp'
    __table_args__ = (
        Index('m_feedvalu_comitecou2_uix', 'completed', 'item', 'course_id', unique=True),
        {'comment': 'values of the completedstmp'}
    )

    id = Column(BIGINT(10), primary_key=True)
    course_id = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    item = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    completed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    tmp_completed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    value = Column(LONGTEXT, nullable=False)


class MFileConversion(Base):
    __tablename__ = 'm_file_conversion'
    __table_args__ = {'comment': 'Table to track file conversions.'}

    id = Column(BIGINT(10), primary_key=True)
    usermodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    sourcefileid = Column(BIGINT(10), nullable=False, index=True)
    targetformat = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    status = Column(BIGINT(10), server_default=text("'0'"))
    statusmessage = Column(LONGTEXT)
    converter = Column(String(255, 'utf8mb4_bin'))
    destfileid = Column(BIGINT(10), index=True)
    data = Column(LONGTEXT)


class MFile(Base):
    __tablename__ = 'm_files'
    __table_args__ = (
        Index('m_file_comfilconite_ix', 'component', 'filearea', 'contextid', 'itemid'),
        {'comment': 'description of files, content is stored in sha1 file pool'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contenthash = Column(String(40, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    pathnamehash = Column(String(40, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    contextid = Column(BIGINT(10), nullable=False, index=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    filearea = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    filepath = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    filename = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    userid = Column(BIGINT(10), index=True)
    filesize = Column(BIGINT(10), nullable=False)
    mimetype = Column(String(100, 'utf8mb4_bin'))
    status = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    source = Column(LONGTEXT)
    author = Column(String(255, 'utf8mb4_bin'))
    license = Column(String(255, 'utf8mb4_bin'), index=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    referencefileid = Column(BIGINT(10), index=True)


class MFilesReference(Base):
    __tablename__ = 'm_files_reference'
    __table_args__ = (
        Index('m_filerefe_refrep_uix', 'referencehash', 'repositoryid', unique=True),
        {'comment': 'Store files references'}
    )

    id = Column(BIGINT(10), primary_key=True)
    repositoryid = Column(BIGINT(10), nullable=False, index=True)
    lastsync = Column(BIGINT(10))
    reference = Column(LONGTEXT)
    referencehash = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MFilterActive(Base):
    __tablename__ = 'm_filter_active'
    __table_args__ = (
        Index('m_filtacti_confil_uix', 'contextid', 'filter', unique=True),
        {'comment': 'Stores information about which filters are active in which c'}
    )

    id = Column(BIGINT(10), primary_key=True)
    filter = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contextid = Column(BIGINT(10), nullable=False, index=True)
    active = Column(SMALLINT(4), nullable=False)
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MFilterConfig(Base):
    __tablename__ = 'm_filter_config'
    __table_args__ = (
        Index('m_filtconf_confilnam_uix', 'contextid', 'filter', 'name', unique=True),
        {'comment': 'Stores per-context configuration settings for filters which '}
    )

    id = Column(BIGINT(10), primary_key=True)
    filter = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contextid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT)


class MFolder(Base):
    __tablename__ = 'm_folder'
    __table_args__ = {'comment': 'each record is one folder resource'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    revision = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    display = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    showexpanded = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    showdownloadfolder = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    forcedownload = Column(TINYINT(1), nullable=False, server_default=text("'1'"))


class MForum(Base):
    __tablename__ = 'm_forum'
    __table_args__ = {'comment': 'Forums contain and structure discussion'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    type = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'general'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    duedate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    cutoffdate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assessed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assesstimestart = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assesstimefinish = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    scale = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    grade_forum = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    grade_forum_notify = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    maxbytes = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    maxattachments = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    forcesubscribe = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    trackingtype = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    rsstype = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    rssarticles = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    warnafter = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    blockafter = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    blockperiod = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    completiondiscussions = Column(INTEGER(9), nullable=False, server_default=text("'0'"))
    completionreplies = Column(INTEGER(9), nullable=False, server_default=text("'0'"))
    completionposts = Column(INTEGER(9), nullable=False, server_default=text("'0'"))
    displaywordcount = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    lockdiscussionafter = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MForumDigest(Base):
    __tablename__ = 'm_forum_digests'
    __table_args__ = (
        Index('m_forudige_forusemai_uix', 'forum', 'userid', 'maildigest', unique=True),
        {'comment': 'Keeps track of user mail delivery preferences for each forum'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    forum = Column(BIGINT(10), nullable=False, index=True)
    maildigest = Column(TINYINT(1), nullable=False, server_default=text("'-1'"))


class MForumDiscussionSub(Base):
    __tablename__ = 'm_forum_discussion_subs'
    __table_args__ = (
        Index('m_forudiscsubs_usedis_uix', 'userid', 'discussion', unique=True),
        {'comment': 'Users may choose to subscribe and unsubscribe from specific '}
    )

    id = Column(BIGINT(10), primary_key=True)
    forum = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    discussion = Column(BIGINT(10), nullable=False, index=True)
    preference = Column(BIGINT(10), nullable=False, server_default=text("'1'"))


class MForumDiscussion(Base):
    __tablename__ = 'm_forum_discussions'
    __table_args__ = {'comment': 'Forums are composed of discussions'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    forum = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    firstpost = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, server_default=text("'-1'"))
    assessed = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    usermodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timestart = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    pinned = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timelocked = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MForumGrade(Base):
    __tablename__ = 'm_forum_grades'
    __table_args__ = (
        Index('m_forugrad_foriteuse_uix', 'forum', 'itemnumber', 'userid', unique=True),
        {'comment': 'Grading data for forum instances'}
    )

    id = Column(BIGINT(10), primary_key=True)
    forum = Column(BIGINT(10), nullable=False, index=True)
    itemnumber = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    grade = Column(DECIMAL(10, 5))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MForumPost(Base):
    __tablename__ = 'm_forum_posts'
    __table_args__ = {'comment': 'All posts are stored in this table'}

    id = Column(BIGINT(10), primary_key=True)
    discussion = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    parent = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    created = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    modified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    mailed = Column(TINYINT(2), nullable=False, index=True, server_default=text("'0'"))
    subject = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    message = Column(LONGTEXT, nullable=False)
    messageformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    messagetrust = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    attachment = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    totalscore = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    mailnow = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    deleted = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    privatereplyto = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    wordcount = Column(BIGINT(20))
    charcount = Column(BIGINT(20))


class MForumQueue(Base):
    __tablename__ = 'm_forum_queue'
    __table_args__ = {'comment': 'For keeping track of posts that will be mailed in digest for'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    discussionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    postid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MForumRead(Base):
    __tablename__ = 'm_forum_read'
    __table_args__ = (
        Index('m_foruread_posuse_ix', 'postid', 'userid'),
        Index('m_foruread_usedis_ix', 'userid', 'discussionid'),
        Index('m_foruread_usefor_ix', 'userid', 'forumid'),
        {'comment': 'Tracks each users read posts'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    forumid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    discussionid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    postid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    firstread = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastread = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MForumSubscription(Base):
    __tablename__ = 'm_forum_subscriptions'
    __table_args__ = (
        Index('m_forusubs_usefor_uix', 'userid', 'forum', unique=True),
        {'comment': 'Keeps track of who is subscribed to what forum'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    forum = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MForumTrackPref(Base):
    __tablename__ = 'm_forum_track_prefs'
    __table_args__ = (
        Index('m_forutracpref_usefor_ix', 'userid', 'forumid'),
        {'comment': 'Tracks each users untracked forums'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    forumid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MGlossary(Base):
    __tablename__ = 'm_glossary'
    __table_args__ = {'comment': 'all glossaries'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    allowduplicatedentries = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    displayformat = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("'dictionary'"))
    mainglossary = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    showspecial = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    showalphabet = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    showall = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    allowcomments = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    allowprintview = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    usedynalink = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    defaultapproval = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    approvaldisplayformat = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("'default'"))
    globalglossary = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    entbypage = Column(SMALLINT(3), nullable=False, server_default=text("'10'"))
    editalways = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    rsstype = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    rssarticles = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    assessed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assesstimestart = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    assesstimefinish = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    scale = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    completionentries = Column(INTEGER(9), nullable=False, server_default=text("'0'"))


class MGlossaryAlia(Base):
    __tablename__ = 'm_glossary_alias'
    __table_args__ = {'comment': 'entries alias'}

    id = Column(BIGINT(10), primary_key=True)
    entryid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    alias = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MGlossaryCategory(Base):
    __tablename__ = 'm_glossary_categories'
    __table_args__ = {'comment': 'all categories for glossary entries'}

    id = Column(BIGINT(10), primary_key=True)
    glossaryid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    usedynalink = Column(TINYINT(2), nullable=False, server_default=text("'1'"))


class MGlossaryEntry(Base):
    __tablename__ = 'm_glossary_entries'
    __table_args__ = {'comment': 'all glossary entries'}

    id = Column(BIGINT(10), primary_key=True)
    glossaryid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    concept = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    definition = Column(LONGTEXT, nullable=False)
    definitionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    definitiontrust = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    attachment = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    teacherentry = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    sourceglossaryid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    usedynalink = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    casesensitive = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    fullmatch = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    approved = Column(TINYINT(2), nullable=False, server_default=text("'1'"))


class MGlossaryEntriesCategory(Base):
    __tablename__ = 'm_glossary_entries_categories'
    __table_args__ = {'comment': 'categories of each glossary entry'}

    id = Column(BIGINT(10), primary_key=True)
    categoryid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    entryid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MGlossaryFormat(Base):
    __tablename__ = 'm_glossary_formats'
    __table_args__ = {'comment': 'Setting of the display formats'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    popupformatname = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    visible = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    showgroup = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    showtabs = Column(String(100, 'utf8mb4_bin'))
    defaultmode = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    defaulthook = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sortkey = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sortorder = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MGradeCategory(Base):
    __tablename__ = 'm_grade_categories'
    __table_args__ = {'comment': 'This table keeps information about categories, used for grou'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    parent = Column(BIGINT(10), index=True)
    depth = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    path = Column(String(255, 'utf8mb4_bin'))
    fullname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    aggregation = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    keephigh = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    droplow = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    aggregateonlygraded = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    aggregateoutcomes = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    hidden = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MGradeCategoriesHistory(Base):
    __tablename__ = 'm_grade_categories_history'
    __table_args__ = {'comment': 'History of grade_categories'}

    id = Column(BIGINT(10), primary_key=True)
    action = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    oldid = Column(BIGINT(10), nullable=False, index=True)
    source = Column(String(255, 'utf8mb4_bin'))
    timemodified = Column(BIGINT(10), index=True)
    loggeduser = Column(BIGINT(10), index=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    parent = Column(BIGINT(10), index=True)
    depth = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    path = Column(String(255, 'utf8mb4_bin'))
    fullname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    aggregation = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    keephigh = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    droplow = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    aggregateonlygraded = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    aggregateoutcomes = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    aggregatesubcats = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    hidden = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MGradeGrade(Base):
    __tablename__ = 'm_grade_grades'
    __table_args__ = (
        Index('m_gradgrad_locloc_ix', 'locked', 'locktime'),
        Index('m_gradgrad_useite_uix', 'userid', 'itemid', unique=True),
        {'comment': 'grade_grades  This table keeps individual grades for each us'}
    )

    id = Column(BIGINT(10), primary_key=True)
    itemid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    rawgrade = Column(DECIMAL(10, 5))
    rawgrademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
    rawgrademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    rawscaleid = Column(BIGINT(10), index=True)
    usermodified = Column(BIGINT(10), index=True)
    finalgrade = Column(DECIMAL(10, 5))
    hidden = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locked = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locktime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    exported = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    overridden = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    excluded = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    feedback = Column(LONGTEXT)
    feedbackformat = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    information = Column(LONGTEXT)
    informationformat = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10))
    timemodified = Column(BIGINT(10))
    aggregationstatus = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("'unknown'"))
    aggregationweight = Column(DECIMAL(10, 5))


class MGradeGradesHistory(Base):
    __tablename__ = 'm_grade_grades_history'
    __table_args__ = (
        Index('m_gradgradhist_useitetim_ix', 'userid', 'itemid', 'timemodified'),
        {'comment': 'History table'}
    )

    id = Column(BIGINT(10), primary_key=True)
    action = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    oldid = Column(BIGINT(10), nullable=False, index=True)
    source = Column(String(255, 'utf8mb4_bin'))
    timemodified = Column(BIGINT(10), index=True)
    loggeduser = Column(BIGINT(10), index=True)
    itemid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    rawgrade = Column(DECIMAL(10, 5))
    rawgrademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
    rawgrademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    rawscaleid = Column(BIGINT(10), index=True)
    usermodified = Column(BIGINT(10), index=True)
    finalgrade = Column(DECIMAL(10, 5))
    hidden = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locked = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locktime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    exported = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    overridden = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    excluded = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    feedback = Column(LONGTEXT)
    feedbackformat = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    information = Column(LONGTEXT)
    informationformat = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MGradeImportNewitem(Base):
    __tablename__ = 'm_grade_import_newitem'
    __table_args__ = {'comment': 'temporary table for storing new grade_item names from grade '}

    id = Column(BIGINT(10), primary_key=True)
    itemname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    importcode = Column(BIGINT(10), nullable=False)
    importer = Column(BIGINT(10), nullable=False, index=True)


class MGradeImportValue(Base):
    __tablename__ = 'm_grade_import_values'
    __table_args__ = {'comment': 'Temporary table for importing grades'}

    id = Column(BIGINT(10), primary_key=True)
    itemid = Column(BIGINT(10), index=True)
    newgradeitem = Column(BIGINT(10), index=True)
    userid = Column(BIGINT(10), nullable=False)
    finalgrade = Column(DECIMAL(10, 5))
    feedback = Column(LONGTEXT)
    importcode = Column(BIGINT(10), nullable=False)
    importer = Column(BIGINT(10), index=True)
    importonlyfeedback = Column(TINYINT(1), server_default=text("'0'"))


class MGradeItem(Base):
    __tablename__ = 'm_grade_items'
    __table_args__ = (
        Index('m_graditem_itenee_ix', 'itemtype', 'needsupdate'),
        Index('m_graditem_locloc_ix', 'locked', 'locktime'),
        Index('m_graditem_idncou_ix', 'idnumber', 'courseid'),
        {'comment': 'This table keeps information about gradeable items (ie colum'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), index=True)
    categoryid = Column(BIGINT(10), index=True)
    itemname = Column(String(255, 'utf8mb4_bin'))
    itemtype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemmodule = Column(String(30, 'utf8mb4_bin'))
    iteminstance = Column(BIGINT(10))
    itemnumber = Column(BIGINT(10))
    iteminfo = Column(LONGTEXT)
    idnumber = Column(String(255, 'utf8mb4_bin'))
    calculation = Column(LONGTEXT)
    gradetype = Column(SMALLINT(4), nullable=False, index=True, server_default=text("'1'"))
    grademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
    grademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    scaleid = Column(BIGINT(10), index=True)
    outcomeid = Column(BIGINT(10), index=True)
    gradepass = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    multfactor = Column(DECIMAL(10, 5), nullable=False, server_default=text("'1.00000'"))
    plusfactor = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    aggregationcoef = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    aggregationcoef2 = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    display = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    decimals = Column(TINYINT(1))
    hidden = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locked = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locktime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    needsupdate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    weightoverride = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10))
    timemodified = Column(BIGINT(10))


class MGradeItemsHistory(Base):
    __tablename__ = 'm_grade_items_history'
    __table_args__ = {'comment': 'History of grade_items'}

    id = Column(BIGINT(10), primary_key=True)
    action = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    oldid = Column(BIGINT(10), nullable=False, index=True)
    source = Column(String(255, 'utf8mb4_bin'))
    timemodified = Column(BIGINT(10), index=True)
    loggeduser = Column(BIGINT(10), index=True)
    courseid = Column(BIGINT(10), index=True)
    categoryid = Column(BIGINT(10), index=True)
    itemname = Column(String(255, 'utf8mb4_bin'))
    itemtype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemmodule = Column(String(30, 'utf8mb4_bin'))
    iteminstance = Column(BIGINT(10))
    itemnumber = Column(BIGINT(10))
    iteminfo = Column(LONGTEXT)
    idnumber = Column(String(255, 'utf8mb4_bin'))
    calculation = Column(LONGTEXT)
    gradetype = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    grademax = Column(DECIMAL(10, 5), nullable=False, server_default=text("'100.00000'"))
    grademin = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    scaleid = Column(BIGINT(10), index=True)
    outcomeid = Column(BIGINT(10), index=True)
    gradepass = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    multfactor = Column(DECIMAL(10, 5), nullable=False, server_default=text("'1.00000'"))
    plusfactor = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    aggregationcoef = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    aggregationcoef2 = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    hidden = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locked = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    locktime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    needsupdate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    display = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    decimals = Column(TINYINT(1))
    weightoverride = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MGradeLetter(Base):
    __tablename__ = 'm_grade_letters'
    __table_args__ = (
        Index('m_gradlett_conlowlet_uix', 'contextid', 'lowerboundary', 'letter', unique=True),
        {'comment': 'Repository for grade letters, for courses and other moodle e'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False)
    lowerboundary = Column(DECIMAL(10, 5), nullable=False)
    letter = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MGradeOutcome(Base):
    __tablename__ = 'm_grade_outcomes'
    __table_args__ = (
        Index('m_gradoutc_cousho_uix', 'courseid', 'shortname', unique=True),
        {'comment': 'This table describes the outcomes used in the system. An out'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), index=True)
    shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    fullname = Column(LONGTEXT, nullable=False)
    scaleid = Column(BIGINT(10), index=True)
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10))
    timemodified = Column(BIGINT(10))
    usermodified = Column(BIGINT(10), index=True)


class MGradeOutcomesCourse(Base):
    __tablename__ = 'm_grade_outcomes_courses'
    __table_args__ = (
        Index('m_gradoutccour_couout_uix', 'courseid', 'outcomeid', unique=True),
        {'comment': 'stores what outcomes are used in what courses.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    outcomeid = Column(BIGINT(10), nullable=False, index=True)


class MGradeOutcomesHistory(Base):
    __tablename__ = 'm_grade_outcomes_history'
    __table_args__ = {'comment': 'History table'}

    id = Column(BIGINT(10), primary_key=True)
    action = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    oldid = Column(BIGINT(10), nullable=False, index=True)
    source = Column(String(255, 'utf8mb4_bin'))
    timemodified = Column(BIGINT(10), index=True)
    loggeduser = Column(BIGINT(10), index=True)
    courseid = Column(BIGINT(10), index=True)
    shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    fullname = Column(LONGTEXT, nullable=False)
    scaleid = Column(BIGINT(10), index=True)
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MGradeSetting(Base):
    __tablename__ = 'm_grade_settings'
    __table_args__ = (
        Index('m_gradsett_counam_uix', 'courseid', 'name', unique=True),
        {'comment': 'gradebook settings'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT)


class MGradingArea(Base):
    __tablename__ = 'm_grading_areas'
    __table_args__ = (
        Index('m_gradarea_concomare_uix', 'contextid', 'component', 'areaname', unique=True),
        {'comment': 'Identifies gradable areas where advanced grading can happen.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    areaname = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    activemethod = Column(String(100, 'utf8mb4_bin'))


class MGradingDefinition(Base):
    __tablename__ = 'm_grading_definitions'
    __table_args__ = (
        Index('m_graddefi_aremet_uix', 'areaid', 'method', unique=True),
        {'comment': 'Contains the basic information about an advanced grading for'}
    )

    id = Column(BIGINT(10), primary_key=True)
    areaid = Column(BIGINT(10), nullable=False, index=True)
    method = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2))
    status = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    copiedfromid = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    usercreated = Column(BIGINT(10), nullable=False, index=True)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False, index=True)
    timecopied = Column(BIGINT(10), server_default=text("'0'"))
    options = Column(LONGTEXT)


class MGradingInstance(Base):
    __tablename__ = 'm_grading_instances'
    __table_args__ = {'comment': 'Grading form instance is an assessment record for one gradab'}

    id = Column(BIGINT(10), primary_key=True)
    definitionid = Column(BIGINT(10), nullable=False, index=True)
    raterid = Column(BIGINT(10), nullable=False, index=True)
    itemid = Column(BIGINT(10))
    rawgrade = Column(DECIMAL(10, 5))
    status = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    feedback = Column(LONGTEXT)
    feedbackformat = Column(TINYINT(2))
    timemodified = Column(BIGINT(10), nullable=False)


class MGradingformGuideComment(Base):
    __tablename__ = 'm_gradingform_guide_comments'
    __table_args__ = {'comment': 'frequently used comments used in marking guide'}

    id = Column(BIGINT(10), primary_key=True)
    definitionid = Column(BIGINT(10), nullable=False, index=True)
    sortorder = Column(BIGINT(10), nullable=False)
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2))


class MGradingformGuideCriterion(Base):
    __tablename__ = 'm_gradingform_guide_criteria'
    __table_args__ = {'comment': 'Stores the rows of the criteria grid.'}

    id = Column(BIGINT(10), primary_key=True)
    definitionid = Column(BIGINT(10), nullable=False, index=True)
    sortorder = Column(BIGINT(10), nullable=False)
    shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2))
    descriptionmarkers = Column(LONGTEXT)
    descriptionmarkersformat = Column(TINYINT(2))
    maxscore = Column(DECIMAL(10, 5), nullable=False)


class MGradingformGuideFilling(Base):
    __tablename__ = 'm_gradingform_guide_fillings'
    __table_args__ = (
        Index('m_gradguidfill_inscri_uix', 'instanceid', 'criterionid', unique=True),
        {'comment': 'Stores the data of how the guide is filled by a particular r'}
    )

    id = Column(BIGINT(10), primary_key=True)
    instanceid = Column(BIGINT(10), nullable=False, index=True)
    criterionid = Column(BIGINT(10), nullable=False, index=True)
    remark = Column(LONGTEXT)
    remarkformat = Column(TINYINT(2))
    score = Column(DECIMAL(10, 5), nullable=False)


class MGradingformRubricCriterion(Base):
    __tablename__ = 'm_gradingform_rubric_criteria'
    __table_args__ = {'comment': 'Stores the rows of the rubric grid.'}

    id = Column(BIGINT(10), primary_key=True)
    definitionid = Column(BIGINT(10), nullable=False, index=True)
    sortorder = Column(BIGINT(10), nullable=False)
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2))


class MGradingformRubricFilling(Base):
    __tablename__ = 'm_gradingform_rubric_fillings'
    __table_args__ = (
        Index('m_gradrubrfill_inscri_uix', 'instanceid', 'criterionid', unique=True),
        {'comment': 'Stores the data of how the rubric is filled by a particular '}
    )

    id = Column(BIGINT(10), primary_key=True)
    instanceid = Column(BIGINT(10), nullable=False, index=True)
    criterionid = Column(BIGINT(10), nullable=False, index=True)
    levelid = Column(BIGINT(10), index=True)
    remark = Column(LONGTEXT)
    remarkformat = Column(TINYINT(2))


class MGradingformRubricLevel(Base):
    __tablename__ = 'm_gradingform_rubric_levels'
    __table_args__ = {'comment': 'Stores the columns of the rubric grid.'}

    id = Column(BIGINT(10), primary_key=True)
    criterionid = Column(BIGINT(10), nullable=False, index=True)
    score = Column(DECIMAL(10, 5), nullable=False)
    definition = Column(LONGTEXT)
    definitionformat = Column(BIGINT(10))


class MGrouping(Base):
    __tablename__ = 'm_groupings'
    __table_args__ = {'comment': 'A grouping is a collection of groups. WAS: groups_groupings'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    idnumber = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    configdata = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MGroupingsGroup(Base):
    __tablename__ = 'm_groupings_groups'
    __table_args__ = {'comment': 'Link a grouping to a group (note, groups can be in multiple '}

    id = Column(BIGINT(10), primary_key=True)
    groupingid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeadded = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MGroup(Base):
    __tablename__ = 'm_groups'
    __table_args__ = {'comment': 'Each record represents a group.'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    idnumber = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    name = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    enrolmentkey = Column(String(50, 'utf8mb4_bin'))
    picture = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MGroupsMember(Base):
    __tablename__ = 'm_groups_members'
    __table_args__ = (
        Index('m_groumemb_usegro_uix', 'userid', 'groupid', unique=True),
        {'comment': 'Link a user to a group.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    groupid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeadded = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MH5p(Base):
    __tablename__ = 'm_h5p'
    __table_args__ = {'comment': 'Stores H5P content information'}

    id = Column(BIGINT(10), primary_key=True)
    jsoncontent = Column(LONGTEXT, nullable=False)
    mainlibraryid = Column(BIGINT(10), nullable=False, index=True)
    displayoptions = Column(SMALLINT(4))
    pathnamehash = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contenthash = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    filtered = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MH5pContentsLibrary(Base):
    __tablename__ = 'm_h5p_contents_libraries'
    __table_args__ = {'comment': 'Store which library is used in which content.'}

    id = Column(BIGINT(10), primary_key=True)
    h5pid = Column(BIGINT(10), nullable=False, index=True)
    libraryid = Column(BIGINT(10), nullable=False, index=True)
    dependencytype = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    dropcss = Column(TINYINT(1), nullable=False)
    weight = Column(BIGINT(10), nullable=False)


class MH5pLibrary(Base):
    __tablename__ = 'm_h5p_libraries'
    __table_args__ = (
        Index('m_h5plibr_macmajminpatrun_ix', 'machinename', 'majorversion', 'minorversion', 'patchversion', 'runnable'),
        {'comment': 'Stores information about libraries used by H5P content.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    machinename = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    title = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    majorversion = Column(SMALLINT(4), nullable=False)
    minorversion = Column(SMALLINT(4), nullable=False)
    patchversion = Column(SMALLINT(4), nullable=False)
    runnable = Column(TINYINT(1), nullable=False)
    fullscreen = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    embedtypes = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    preloadedjs = Column(LONGTEXT)
    preloadedcss = Column(LONGTEXT)
    droplibrarycss = Column(LONGTEXT)
    semantics = Column(LONGTEXT)
    addto = Column(LONGTEXT)
    coremajor = Column(SMALLINT(4))
    coreminor = Column(SMALLINT(4))
    metadatasettings = Column(LONGTEXT)
    tutorial = Column(LONGTEXT)
    example = Column(LONGTEXT)
    enabled = Column(TINYINT(1), server_default=text("'1'"))


class MH5pLibrariesCachedasset(Base):
    __tablename__ = 'm_h5p_libraries_cachedassets'
    __table_args__ = {'comment': 'H5P cached library assets'}

    id = Column(BIGINT(10), primary_key=True)
    libraryid = Column(BIGINT(10), nullable=False, index=True)
    hash = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MH5pLibraryDependency(Base):
    __tablename__ = 'm_h5p_library_dependencies'
    __table_args__ = {'comment': 'Stores H5P library dependencies'}

    id = Column(BIGINT(10), primary_key=True)
    libraryid = Column(BIGINT(10), nullable=False, index=True)
    requiredlibraryid = Column(BIGINT(10), nullable=False, index=True)
    dependencytype = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MH5pactivity(Base):
    __tablename__ = 'm_h5pactivity'
    __table_args__ = {'comment': 'Stores the h5pactivity activity module instances.'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    grade = Column(BIGINT(10), server_default=text("'0'"))
    displayoptions = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    enabletracking = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    grademethod = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    reviewmode = Column(SMALLINT(4), server_default=text("'1'"))


class MH5pactivityAttempt(Base):
    __tablename__ = 'm_h5pactivity_attempts'
    __table_args__ = (
        Index('m_h5paatte_h5puse_ix', 'h5pactivityid', 'userid'),
        Index('m_h5paatte_h5ptim_ix', 'h5pactivityid', 'timecreated'),
        Index('m_h5paatte_h5puseatt_uix', 'h5pactivityid', 'userid', 'attempt', unique=True),
        {'comment': 'Users attempts inside H5P activities'}
    )

    id = Column(BIGINT(10), primary_key=True)
    h5pactivityid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(20), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False, index=True)
    timemodified = Column(BIGINT(10), nullable=False)
    attempt = Column(MEDIUMINT(6), nullable=False, server_default=text("'1'"))
    rawscore = Column(BIGINT(10), server_default=text("'0'"))
    maxscore = Column(BIGINT(10), server_default=text("'0'"))
    scaled = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    duration = Column(BIGINT(10), server_default=text("'0'"))
    completion = Column(TINYINT(1))
    success = Column(TINYINT(1))


class MH5pactivityAttemptsResult(Base):
    __tablename__ = 'm_h5pactivity_attempts_results'
    __table_args__ = (
        Index('m_h5paatteresu_atttim_ix', 'attemptid', 'timecreated'),
        {'comment': 'H5Pactivities_attempts tracking info'}
    )

    id = Column(BIGINT(10), primary_key=True)
    attemptid = Column(BIGINT(10), nullable=False, index=True)
    subcontent = Column(String(128, 'utf8mb4_bin'))
    timecreated = Column(BIGINT(10), nullable=False)
    interactiontype = Column(String(128, 'utf8mb4_bin'))
    description = Column(LONGTEXT)
    correctpattern = Column(LONGTEXT)
    response = Column(LONGTEXT, nullable=False)
    additionals = Column(LONGTEXT)
    rawscore = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    maxscore = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    duration = Column(BIGINT(10), server_default=text("'0'"))
    completion = Column(TINYINT(1))
    success = Column(TINYINT(1))


class MImscp(Base):
    __tablename__ = 'm_imscp'
    __table_args__ = {'comment': 'each record is one imscp resource'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    revision = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    keepold = Column(BIGINT(10), nullable=False, server_default=text("'-1'"))
    structure = Column(LONGTEXT)
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MInfectedFile(Base):
    __tablename__ = 'm_infected_files'
    __table_args__ = {'comment': 'Table to store infected file details.'}

    id = Column(BIGINT(10), primary_key=True)
    filename = Column(LONGTEXT, nullable=False)
    quarantinedfile = Column(LONGTEXT)
    userid = Column(BIGINT(10), nullable=False, index=True)
    reason = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MLabel(Base):
    __tablename__ = 'm_label'
    __table_args__ = {'comment': 'Defines labels'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MLesson(Base):
    __tablename__ = 'm_lesson'
    __table_args__ = {'comment': 'Defines lesson'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    practice = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    modattempts = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    usepassword = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    password = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    dependency = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    conditions = Column(LONGTEXT, nullable=False)
    grade = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    custom = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    ongoing = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    usemaxgrade = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    maxanswers = Column(SMALLINT(3), nullable=False, server_default=text("'4'"))
    maxattempts = Column(SMALLINT(3), nullable=False, server_default=text("'5'"))
    review = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    nextpagedefault = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    feedback = Column(SMALLINT(3), nullable=False, server_default=text("'1'"))
    minquestions = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    maxpages = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    timelimit = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    retake = Column(SMALLINT(3), nullable=False, server_default=text("'1'"))
    activitylink = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    mediafile = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    mediaheight = Column(BIGINT(10), nullable=False, server_default=text("'100'"))
    mediawidth = Column(BIGINT(10), nullable=False, server_default=text("'650'"))
    mediaclose = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    slideshow = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    width = Column(BIGINT(10), nullable=False, server_default=text("'640'"))
    height = Column(BIGINT(10), nullable=False, server_default=text("'480'"))
    bgcolor = Column(String(7, 'utf8mb4_bin'), nullable=False, server_default=text("'#FFFFFF'"))
    displayleft = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    displayleftif = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    progressbar = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    available = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    deadline = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    completionendreached = Column(TINYINT(1), server_default=text("'0'"))
    completiontimespent = Column(BIGINT(11), server_default=text("'0'"))
    allowofflineattempts = Column(TINYINT(1), server_default=text("'0'"))


class MLessonAnswer(Base):
    __tablename__ = 'm_lesson_answers'
    __table_args__ = {'comment': 'Defines lesson_answers'}

    id = Column(BIGINT(10), primary_key=True)
    lessonid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    pageid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    jumpto = Column(BIGINT(11), nullable=False, server_default=text("'0'"))
    grade = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    score = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    flags = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    answer = Column(LONGTEXT)
    answerformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    response = Column(LONGTEXT)
    responseformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MLessonAttempt(Base):
    __tablename__ = 'm_lesson_attempts'
    __table_args__ = {'comment': 'Defines lesson_attempts'}

    id = Column(BIGINT(10), primary_key=True)
    lessonid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    pageid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    answerid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    retry = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    correct = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    useranswer = Column(LONGTEXT)
    timeseen = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MLessonBranch(Base):
    __tablename__ = 'm_lesson_branch'
    __table_args__ = {'comment': 'branches for each lesson/user'}

    id = Column(BIGINT(10), primary_key=True)
    lessonid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    pageid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    retry = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    flag = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    timeseen = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    nextpageid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MLessonGrade(Base):
    __tablename__ = 'm_lesson_grades'
    __table_args__ = {'comment': 'Defines lesson_grades'}

    id = Column(BIGINT(10), primary_key=True)
    lessonid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    grade = Column(Float(asdecimal=True), nullable=False, server_default=text("'0'"))
    late = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    completed = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MLessonOverride(Base):
    __tablename__ = 'm_lesson_overrides'
    __table_args__ = {'comment': 'The overrides to lesson settings.'}

    id = Column(BIGINT(10), primary_key=True)
    lessonid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), index=True)
    userid = Column(BIGINT(10), index=True)
    available = Column(BIGINT(10))
    deadline = Column(BIGINT(10))
    timelimit = Column(BIGINT(10))
    review = Column(SMALLINT(3))
    maxattempts = Column(SMALLINT(3))
    retake = Column(SMALLINT(3))
    password = Column(String(32, 'utf8mb4_bin'))


class MLessonPage(Base):
    __tablename__ = 'm_lesson_pages'
    __table_args__ = {'comment': 'Defines lesson_pages'}

    id = Column(BIGINT(10), primary_key=True)
    lessonid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    prevpageid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    nextpageid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    qtype = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    qoption = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    layout = Column(SMALLINT(3), nullable=False, server_default=text("'1'"))
    display = Column(SMALLINT(3), nullable=False, server_default=text("'1'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    title = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contents = Column(LONGTEXT, nullable=False)
    contentsformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MLessonTimer(Base):
    __tablename__ = 'm_lesson_timer'
    __table_args__ = {'comment': 'lesson timer for each lesson'}

    id = Column(BIGINT(10), primary_key=True)
    lessonid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    starttime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lessontime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    completed = Column(TINYINT(1), server_default=text("'0'"))
    timemodifiedoffline = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MLicense(Base):
    __tablename__ = 'm_license'
    __table_args__ = {'comment': 'store licenses used by moodle'}

    id = Column(BIGINT(10), primary_key=True)
    shortname = Column(String(255, 'utf8mb4_bin'))
    fullname = Column(LONGTEXT)
    source = Column(String(255, 'utf8mb4_bin'))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    version = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    custom = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    sortorder = Column(MEDIUMINT(5), nullable=False, server_default=text("'0'"))


class MLockDb(Base):
    __tablename__ = 'm_lock_db'
    __table_args__ = {'comment': 'Stores active and inactive lock types for db locking method.'}

    id = Column(BIGINT(10), primary_key=True)
    resourcekey = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    expires = Column(BIGINT(10), index=True)
    owner = Column(String(36, 'utf8mb4_bin'), index=True)


class MLog(Base):
    __tablename__ = 'm_log'
    __table_args__ = (
        Index('m_log_coumodact_ix', 'course', 'module', 'action'),
        Index('m_log_usecou_ix', 'userid', 'course'),
        {'comment': 'Every action is logged as far as possible'}
    )

    id = Column(BIGINT(10), primary_key=True)
    time = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    ip = Column(String(45, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    module = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    cmid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    action = Column(String(40, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    url = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    info = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MLogDisplay(Base):
    __tablename__ = 'm_log_display'
    __table_args__ = (
        Index('m_logdisp_modact_uix', 'module', 'action', unique=True),
        {'comment': 'For a particular module/action, specifies a moodle table/fie'}
    )

    id = Column(BIGINT(10), primary_key=True)
    module = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    action = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    mtable = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    field = Column(String(200, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MLogQuery(Base):
    __tablename__ = 'm_log_queries'
    __table_args__ = {'comment': 'Logged database queries.'}

    id = Column(BIGINT(10), primary_key=True)
    qtype = Column(MEDIUMINT(5), nullable=False)
    sqltext = Column(LONGTEXT, nullable=False)
    sqlparams = Column(LONGTEXT)
    error = Column(MEDIUMINT(5), nullable=False, server_default=text("'0'"))
    info = Column(LONGTEXT)
    backtrace = Column(LONGTEXT)
    exectime = Column(DECIMAL(10, 5), nullable=False)
    timelogged = Column(BIGINT(10), nullable=False)


class MLogstoreStandardLog(Base):
    __tablename__ = 'm_logstore_standard_log'
    __table_args__ = (
        Index('m_logsstanlog_useconconcrue_ix', 'userid', 'contextlevel', 'contextinstanceid', 'crud', 'edulevel', 'timecreated'),
        Index('m_logsstanlog_couanotim_ix', 'courseid', 'anonymous', 'timecreated'),
        {'comment': 'Standard log table'}
    )

    id = Column(BIGINT(10), primary_key=True)
    eventname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    action = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    target = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    objecttable = Column(String(50, 'utf8mb4_bin'))
    objectid = Column(BIGINT(10))
    crud = Column(String(1, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    edulevel = Column(TINYINT(1), nullable=False)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    contextlevel = Column(BIGINT(10), nullable=False)
    contextinstanceid = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False)
    courseid = Column(BIGINT(10))
    relateduserid = Column(BIGINT(10))
    anonymous = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    other = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, index=True)
    origin = Column(String(10, 'utf8mb4_bin'))
    ip = Column(String(45, 'utf8mb4_bin'))
    realuserid = Column(BIGINT(10))


class MLti(Base):
    __tablename__ = 'm_lti'
    __table_args__ = {'comment': 'This table contains Basic LTI activities instances'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    typeid = Column(BIGINT(10))
    toolurl = Column(LONGTEXT, nullable=False)
    securetoolurl = Column(LONGTEXT)
    instructorchoicesendname = Column(TINYINT(1))
    instructorchoicesendemailaddr = Column(TINYINT(1))
    instructorchoiceallowroster = Column(TINYINT(1))
    instructorchoiceallowsetting = Column(TINYINT(1))
    instructorcustomparameters = Column(LONGTEXT)
    instructorchoiceacceptgrades = Column(TINYINT(1))
    grade = Column(BIGINT(10), nullable=False, server_default=text("'100'"))
    launchcontainer = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    resourcekey = Column(String(255, 'utf8mb4_bin'))
    password = Column(String(255, 'utf8mb4_bin'))
    debuglaunch = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    showtitlelaunch = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    showdescriptionlaunch = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    servicesalt = Column(String(40, 'utf8mb4_bin'))
    icon = Column(LONGTEXT)
    secureicon = Column(LONGTEXT)


class MLtiAccessToken(Base):
    __tablename__ = 'm_lti_access_tokens'
    __table_args__ = {'comment': 'Security tokens for accessing of LTI services'}

    id = Column(BIGINT(10), primary_key=True)
    typeid = Column(BIGINT(10), nullable=False, index=True)
    scope = Column(LONGTEXT, nullable=False)
    token = Column(String(128, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    validuntil = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    lastaccess = Column(BIGINT(10))


class MLtiSubmission(Base):
    __tablename__ = 'm_lti_submission'
    __table_args__ = {'comment': 'Keeps track of individual submissions for LTI activities.'}

    id = Column(BIGINT(10), primary_key=True)
    ltiid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False)
    datesubmitted = Column(BIGINT(10), nullable=False)
    dateupdated = Column(BIGINT(10), nullable=False)
    gradepercent = Column(DECIMAL(10, 5), nullable=False)
    originalgrade = Column(DECIMAL(10, 5), nullable=False)
    launchid = Column(BIGINT(10), nullable=False)
    state = Column(TINYINT(2), nullable=False)


class MLtiToolProxy(Base):
    __tablename__ = 'm_lti_tool_proxies'
    __table_args__ = {'comment': 'LTI tool proxy registrations'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'Tool Provider'"))
    regurl = Column(LONGTEXT)
    state = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    guid = Column(String(255, 'utf8mb4_bin'), unique=True)
    secret = Column(String(255, 'utf8mb4_bin'))
    vendorcode = Column(String(255, 'utf8mb4_bin'))
    capabilityoffered = Column(LONGTEXT, nullable=False)
    serviceoffered = Column(LONGTEXT, nullable=False)
    toolproxy = Column(LONGTEXT)
    createdby = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MLtiToolSetting(Base):
    __tablename__ = 'm_lti_tool_settings'
    __table_args__ = {'comment': 'LTI tool setting values'}

    id = Column(BIGINT(10), primary_key=True)
    toolproxyid = Column(BIGINT(10), nullable=False, index=True)
    typeid = Column(BIGINT(10), index=True)
    course = Column(BIGINT(10), index=True)
    coursemoduleid = Column(BIGINT(10), index=True)
    settings = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MLtiType(Base):
    __tablename__ = 'm_lti_types'
    __table_args__ = {'comment': 'Basic LTI pre-configured activities'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'basiclti Activity'"))
    baseurl = Column(LONGTEXT, nullable=False)
    tooldomain = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    state = Column(TINYINT(2), nullable=False, server_default=text("'2'"))
    course = Column(BIGINT(10), nullable=False, index=True)
    coursevisible = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    ltiversion = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    clientid = Column(String(255, 'utf8mb4_bin'), unique=True)
    toolproxyid = Column(BIGINT(10))
    enabledcapability = Column(LONGTEXT)
    parameter = Column(LONGTEXT)
    icon = Column(LONGTEXT)
    secureicon = Column(LONGTEXT)
    createdby = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    description = Column(LONGTEXT)


class MLtiTypesConfig(Base):
    __tablename__ = 'm_lti_types_config'
    __table_args__ = {'comment': 'Basic LTI types configuration'}

    id = Column(BIGINT(10), primary_key=True)
    typeid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT, nullable=False)


class MLtiserviceGradebookservice(Base):
    __tablename__ = 'm_ltiservice_gradebookservices'
    __table_args__ = (
        Index('m_ltisgrad_gracou_ix', 'gradeitemid', 'courseid'),
        {'comment': 'This file records the grade items created by the LTI Gradebo'}
    )

    id = Column(BIGINT(10), primary_key=True)
    gradeitemid = Column(BIGINT(10), nullable=False)
    courseid = Column(BIGINT(10), nullable=False)
    toolproxyid = Column(BIGINT(10))
    typeid = Column(BIGINT(10))
    baseurl = Column(LONGTEXT)
    ltilinkid = Column(BIGINT(10), index=True)
    resourceid = Column(String(512, 'utf8mb4_bin'))
    tag = Column(String(255, 'utf8mb4_bin'))


class MMessage(Base):
    __tablename__ = 'm_message'
    __table_args__ = (
        Index('m_mess_usetimnot2_ix', 'useridto', 'timeusertodeleted', 'notification'),
        Index('m_mess_useusetimtim_ix', 'useridfrom', 'useridto', 'timeuserfromdeleted', 'timeusertodeleted'),
        Index('m_mess_usetimnot_ix', 'useridfrom', 'timeuserfromdeleted', 'notification'),
        {'comment': 'Stores all unread messages'}
    )

    id = Column(BIGINT(10), primary_key=True)
    useridfrom = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    useridto = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    subject = Column(LONGTEXT)
    fullmessage = Column(LONGTEXT)
    fullmessageformat = Column(SMALLINT(4), server_default=text("'0'"))
    fullmessagehtml = Column(LONGTEXT)
    smallmessage = Column(LONGTEXT)
    notification = Column(TINYINT(1), server_default=text("'0'"))
    contexturl = Column(LONGTEXT)
    contexturlname = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeuserfromdeleted = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeusertodeleted = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    component = Column(String(100, 'utf8mb4_bin'))
    eventtype = Column(String(100, 'utf8mb4_bin'))
    customdata = Column(LONGTEXT)


class MMessageAirnotifierDevice(Base):
    __tablename__ = 'm_message_airnotifier_devices'
    __table_args__ = {'comment': 'Store information about the devices registered in Airnotifie'}

    id = Column(BIGINT(10), primary_key=True)
    userdeviceid = Column(BIGINT(10), nullable=False, unique=True)
    enable = Column(TINYINT(1), nullable=False, server_default=text("'1'"))


class MMessageContactRequest(Base):
    __tablename__ = 'm_message_contact_requests'
    __table_args__ = (
        Index('m_messcontrequ_usereq_uix', 'userid', 'requesteduserid', unique=True),
        {'comment': 'Maintains list of contact requests between users'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    requesteduserid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)


class MMessageContact(Base):
    __tablename__ = 'm_message_contacts'
    __table_args__ = (
        Index('m_messcont_usecon_uix', 'userid', 'contactid', unique=True),
        {'comment': 'Maintains lists of contacts between users'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    contactid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10))


class MMessageConversationAction(Base):
    __tablename__ = 'm_message_conversation_actions'
    __table_args__ = {'comment': 'Stores all per-user actions on individual conversations'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    conversationid = Column(BIGINT(10), nullable=False, index=True)
    action = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)


class MMessageConversationMember(Base):
    __tablename__ = 'm_message_conversation_members'
    __table_args__ = {'comment': 'Stores all members in a conversations'}

    id = Column(BIGINT(10), primary_key=True)
    conversationid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)


class MMessageConversation(Base):
    __tablename__ = 'm_message_conversations'
    __table_args__ = (
        Index('m_messconv_comiteitecon_ix', 'component', 'itemtype', 'itemid', 'contextid'),
        {'comment': 'Stores all message conversations'}
    )

    id = Column(BIGINT(10), primary_key=True)
    type = Column(BIGINT(10), nullable=False, index=True, server_default=text("'1'"))
    name = Column(String(255, 'utf8mb4_bin'))
    convhash = Column(String(40, 'utf8mb4_bin'), index=True)
    component = Column(String(100, 'utf8mb4_bin'))
    itemtype = Column(String(100, 'utf8mb4_bin'))
    itemid = Column(BIGINT(10))
    contextid = Column(BIGINT(10), index=True)
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10))


class MMessageEmailMessage(Base):
    __tablename__ = 'm_message_email_messages'
    __table_args__ = {'comment': 'Keeps track of what emails to send in an email digest'}

    id = Column(BIGINT(10), primary_key=True)
    useridto = Column(BIGINT(10), nullable=False, index=True)
    conversationid = Column(BIGINT(10), nullable=False, index=True)
    messageid = Column(BIGINT(10), nullable=False, index=True)


class MMessagePopup(Base):
    __tablename__ = 'm_message_popup'
    __table_args__ = (
        Index('m_messpopu_mesisr_uix', 'messageid', 'isread', unique=True),
        {'comment': 'Keep state of notifications for the popup message processor'}
    )

    id = Column(BIGINT(10), primary_key=True)
    messageid = Column(BIGINT(10), nullable=False)
    isread = Column(TINYINT(1), nullable=False, index=True, server_default=text("'0'"))


class MMessagePopupNotification(Base):
    __tablename__ = 'm_message_popup_notifications'
    __table_args__ = {'comment': 'List of notifications to display in the message output popup'}

    id = Column(BIGINT(10), primary_key=True)
    notificationid = Column(BIGINT(10), nullable=False, index=True)


class MMessageProcessor(Base):
    __tablename__ = 'm_message_processors'
    __table_args__ = {'comment': 'List of message output plugins'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(166, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'1'"))


class MMessageProvider(Base):
    __tablename__ = 'm_message_providers'
    __table_args__ = (
        Index('m_messprov_comnam_uix', 'component', 'name', unique=True),
        {'comment': 'This table stores the message providers (modules and core sy'}
    )

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    component = Column(String(200, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    capability = Column(String(255, 'utf8mb4_bin'))


class MMessageRead(Base):
    __tablename__ = 'm_message_read'
    __table_args__ = (
        Index('m_messread_usetimnot2_ix', 'useridto', 'timeusertodeleted', 'notification'),
        Index('m_messread_usetimnot_ix', 'useridfrom', 'timeuserfromdeleted', 'notification'),
        Index('m_messread_nottim_ix', 'notification', 'timeread'),
        Index('m_messread_useusetimtim_ix', 'useridfrom', 'useridto', 'timeuserfromdeleted', 'timeusertodeleted'),
        {'comment': 'Stores all messages that have been read'}
    )

    id = Column(BIGINT(10), primary_key=True)
    useridfrom = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    useridto = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    subject = Column(LONGTEXT)
    fullmessage = Column(LONGTEXT)
    fullmessageformat = Column(SMALLINT(4), server_default=text("'0'"))
    fullmessagehtml = Column(LONGTEXT)
    smallmessage = Column(LONGTEXT)
    notification = Column(TINYINT(1), server_default=text("'0'"))
    contexturl = Column(LONGTEXT)
    contexturlname = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeread = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeuserfromdeleted = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeusertodeleted = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    component = Column(String(100, 'utf8mb4_bin'))
    eventtype = Column(String(100, 'utf8mb4_bin'))


class MMessageUserAction(Base):
    __tablename__ = 'm_message_user_actions'
    __table_args__ = (
        Index('m_messuseracti_usemesact_uix', 'userid', 'messageid', 'action', unique=True),
        {'comment': 'Stores all per-user actions on individual messages'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    messageid = Column(BIGINT(10), nullable=False, index=True)
    action = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)


class MMessageUsersBlocked(Base):
    __tablename__ = 'm_message_users_blocked'
    __table_args__ = (
        Index('m_messuserbloc_useblo_uix', 'userid', 'blockeduserid', unique=True),
        {'comment': 'Maintains lists of blocked users'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    blockeduserid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10))


class MMessageinboundDatakey(Base):
    __tablename__ = 'm_messageinbound_datakeys'
    __table_args__ = (
        Index('m_messdata_handat_uix', 'handler', 'datavalue', unique=True),
        {'comment': 'Inbound Message data item secret keys.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    handler = Column(BIGINT(10), nullable=False, index=True)
    datavalue = Column(BIGINT(10), nullable=False)
    datakey = Column(String(64, 'utf8mb4_bin'))
    timecreated = Column(BIGINT(10), nullable=False)
    expires = Column(BIGINT(10))


class MMessageinboundHandler(Base):
    __tablename__ = 'm_messageinbound_handlers'
    __table_args__ = {'comment': 'Inbound Message Handler definitions.'}

    id = Column(BIGINT(10), primary_key=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    classname = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    defaultexpiration = Column(BIGINT(10), nullable=False, server_default=text("'86400'"))
    validateaddress = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MMessageinboundMessagelist(Base):
    __tablename__ = 'm_messageinbound_messagelist'
    __table_args__ = {'comment': 'A list of message IDs for existing replies'}

    id = Column(BIGINT(10), primary_key=True)
    messageid = Column(LONGTEXT, nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    address = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)


class MMessage(Base):
    __tablename__ = 'm_messages'
    __table_args__ = (
        Index('m_mess_contim_ix', 'conversationid', 'timecreated'),
        {'comment': 'Stores all messages'}
    )

    id = Column(BIGINT(10), primary_key=True)
    useridfrom = Column(BIGINT(10), nullable=False, index=True)
    conversationid = Column(BIGINT(10), nullable=False, index=True)
    subject = Column(LONGTEXT)
    fullmessage = Column(LONGTEXT)
    fullmessageformat = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    fullmessagehtml = Column(LONGTEXT)
    smallmessage = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False)
    fullmessagetrust = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    customdata = Column(LONGTEXT)


class MMnetApplication(Base):
    __tablename__ = 'm_mnet_application'
    __table_args__ = {'comment': 'Information about applications on remote hosts'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    display_name = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    xmlrpc_server_url = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sso_land_url = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sso_jump_url = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MMnetHost(Base):
    __tablename__ = 'm_mnet_host'
    __table_args__ = {'comment': 'Information about the local and remote hosts for RPC'}

    id = Column(BIGINT(10), primary_key=True)
    deleted = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    wwwroot = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    ip_address = Column(String(45, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    name = Column(String(80, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    public_key = Column(LONGTEXT, nullable=False)
    public_key_expires = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    transport = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    portno = Column(MEDIUMINT(5), nullable=False, server_default=text("'0'"))
    last_connect_time = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    last_log_id = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    force_theme = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    theme = Column(String(100, 'utf8mb4_bin'))
    applicationid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'1'"))
    sslverification = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MMnetHost2service(Base):
    __tablename__ = 'm_mnet_host2service'
    __table_args__ = (
        Index('m_mnethost_hosser_uix', 'hostid', 'serviceid', unique=True),
        {'comment': 'Information about the services for a given host'}
    )

    id = Column(BIGINT(10), primary_key=True)
    hostid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    serviceid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    publish = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    subscribe = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MMnetLog(Base):
    __tablename__ = 'm_mnet_log'
    __table_args__ = (
        Index('m_mnetlog_hosusecou_ix', 'hostid', 'userid', 'course'),
        {'comment': 'Store session data from users migrating to other sites'}
    )

    id = Column(BIGINT(10), primary_key=True)
    hostid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    remoteid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    time = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    ip = Column(String(45, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    coursename = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    module = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    cmid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    action = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    url = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    info = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MMnetRemoteRpc(Base):
    __tablename__ = 'm_mnet_remote_rpc'
    __table_args__ = {'comment': 'This table describes functions that might be called remotely'}

    id = Column(BIGINT(10), primary_key=True)
    functionname = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    xmlrpcpath = Column(String(80, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    plugintype = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    pluginname = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    enabled = Column(TINYINT(1), nullable=False)


class MMnetRemoteService2rpc(Base):
    __tablename__ = 'm_mnet_remote_service2rpc'
    __table_args__ = (
        Index('m_mnetremoserv_rpcser_uix', 'rpcid', 'serviceid', unique=True),
        {'comment': 'Group functions or methods under a service'}
    )

    id = Column(BIGINT(10), primary_key=True)
    serviceid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    rpcid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MMnetRpc(Base):
    __tablename__ = 'm_mnet_rpc'
    __table_args__ = (
        Index('m_mnetrpc_enaxml_ix', 'enabled', 'xmlrpcpath'),
        {'comment': 'Functions or methods that we may publish or subscribe to'}
    )

    id = Column(BIGINT(10), primary_key=True)
    functionname = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    xmlrpcpath = Column(String(80, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    plugintype = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    pluginname = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    help = Column(LONGTEXT, nullable=False)
    profile = Column(LONGTEXT, nullable=False)
    filename = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    classname = Column(String(150, 'utf8mb4_bin'))
    static = Column(TINYINT(1))


class MMnetService(Base):
    __tablename__ = 'm_mnet_service'
    __table_args__ = {'comment': 'A service is a group of functions'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    apiversion = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    offer = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MMnetService2rpc(Base):
    __tablename__ = 'm_mnet_service2rpc'
    __table_args__ = (
        Index('m_mnetserv_rpcser_uix', 'rpcid', 'serviceid', unique=True),
        {'comment': 'Group functions or methods under a service'}
    )

    id = Column(BIGINT(10), primary_key=True)
    serviceid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    rpcid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MMnetSession(Base):
    __tablename__ = 'm_mnet_session'
    __table_args__ = {'comment': 'Store session data from users migrating to other sites'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    username = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    token = Column(String(40, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    mnethostid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    useragent = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    confirm_timeout = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    session_id = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    expires = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MMnetSsoAccessControl(Base):
    __tablename__ = 'm_mnet_sso_access_control'
    __table_args__ = (
        Index('m_mnetssoaccecont_mneuse_uix', 'mnet_host_id', 'username', unique=True),
        {'comment': 'Users by host permitted (or not) to login from a remote prov'}
    )

    id = Column(BIGINT(10), primary_key=True)
    username = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    mnet_host_id = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    accessctrl = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'allow'"))


class MMnetserviceEnrolCourse(Base):
    __tablename__ = 'm_mnetservice_enrol_courses'
    __table_args__ = (
        Index('m_mnetenrocour_hosrem_uix', 'hostid', 'remoteid', unique=True),
        {'comment': 'Caches the information fetched via XML-RPC about courses on '}
    )

    id = Column(BIGINT(10), primary_key=True)
    hostid = Column(BIGINT(10), nullable=False)
    remoteid = Column(BIGINT(10), nullable=False)
    categoryid = Column(BIGINT(10), nullable=False)
    categoryname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    fullname = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    shortname = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    idnumber = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    summary = Column(LONGTEXT, nullable=False)
    summaryformat = Column(SMALLINT(3), server_default=text("'0'"))
    startdate = Column(BIGINT(10), nullable=False)
    roleid = Column(BIGINT(10), nullable=False)
    rolename = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MMnetserviceEnrolEnrolment(Base):
    __tablename__ = 'm_mnetservice_enrol_enrolments'
    __table_args__ = {'comment': 'Caches the information about enrolments of our local users i'}

    id = Column(BIGINT(10), primary_key=True)
    hostid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    remotecourseid = Column(BIGINT(10), nullable=False)
    rolename = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    enroltime = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    enroltype = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MModule(Base):
    __tablename__ = 'm_modules'
    __table_args__ = {'comment': 'modules available in the site'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(20, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    cron = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastcron = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    search = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    visible = Column(TINYINT(1), nullable=False, server_default=text("'1'"))


class MMyPage(Base):
    __tablename__ = 'm_my_pages'
    __table_args__ = (
        Index('m_mypage_usepri_ix', 'userid', 'private'),
        {'comment': 'Extra user pages for the My Moodle system'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), server_default=text("'0'"))
    name = Column(String(200, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    private = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    sortorder = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))


class MNotification(Base):
    __tablename__ = 'm_notifications'
    __table_args__ = {'comment': 'Stores all notifications'}

    id = Column(BIGINT(10), primary_key=True)
    useridfrom = Column(BIGINT(10), nullable=False, index=True)
    useridto = Column(BIGINT(10), nullable=False, index=True)
    subject = Column(LONGTEXT)
    fullmessage = Column(LONGTEXT)
    fullmessageformat = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    fullmessagehtml = Column(LONGTEXT)
    smallmessage = Column(LONGTEXT)
    component = Column(String(100, 'utf8mb4_bin'))
    eventtype = Column(String(100, 'utf8mb4_bin'))
    contexturl = Column(LONGTEXT)
    contexturlname = Column(LONGTEXT)
    timeread = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False)
    customdata = Column(LONGTEXT)


class MOauth2AccessToken(Base):
    __tablename__ = 'm_oauth2_access_token'
    __table_args__ = {'comment': 'Stores access tokens for system accounts in order to be able'}

    id = Column(BIGINT(10), primary_key=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    issuerid = Column(BIGINT(10), nullable=False, unique=True)
    token = Column(LONGTEXT, nullable=False)
    expires = Column(BIGINT(10), nullable=False)
    scope = Column(LONGTEXT, nullable=False)


class MOauth2Endpoint(Base):
    __tablename__ = 'm_oauth2_endpoint'
    __table_args__ = {'comment': 'Describes the named endpoint for an oauth2 service.'}

    id = Column(BIGINT(10), primary_key=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    url = Column(LONGTEXT, nullable=False)
    issuerid = Column(BIGINT(10), nullable=False, index=True)


class MOauth2Issuer(Base):
    __tablename__ = 'm_oauth2_issuer'
    __table_args__ = {'comment': 'Details for an oauth 2 connect identity issuer.'}

    id = Column(BIGINT(10), primary_key=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    image = Column(LONGTEXT, nullable=False)
    baseurl = Column(LONGTEXT, nullable=False)
    clientid = Column(LONGTEXT, nullable=False)
    clientsecret = Column(LONGTEXT, nullable=False)
    loginscopes = Column(LONGTEXT, nullable=False)
    loginscopesoffline = Column(LONGTEXT, nullable=False)
    loginparams = Column(LONGTEXT, nullable=False)
    loginparamsoffline = Column(LONGTEXT, nullable=False)
    alloweddomains = Column(LONGTEXT, nullable=False)
    scopessupported = Column(LONGTEXT)
    enabled = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    showonloginpage = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    basicauth = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    sortorder = Column(BIGINT(10), nullable=False)
    requireconfirmation = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    servicetype = Column(String(255, 'utf8mb4_bin'))
    loginpagename = Column(String(255, 'utf8mb4_bin'))


class MOauth2RefreshToken(Base):
    __tablename__ = 'm_oauth2_refresh_token'
    __table_args__ = (
        Index('m_oautrefrtoke_useisssco_uix', 'userid', 'issuerid', 'scopehash', unique=True),
        {'comment': 'Stores refresh tokens which can be exchanged for access toke'}
    )

    id = Column(BIGINT(10), primary_key=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    issuerid = Column(BIGINT(10), nullable=False, index=True)
    token = Column(LONGTEXT, nullable=False)
    scopehash = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MOauth2SystemAccount(Base):
    __tablename__ = 'm_oauth2_system_account'
    __table_args__ = {'comment': 'Stored details used to get an access token as a system user '}

    id = Column(BIGINT(10), primary_key=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    issuerid = Column(BIGINT(10), nullable=False, unique=True)
    refreshtoken = Column(LONGTEXT, nullable=False)
    grantedscopes = Column(LONGTEXT, nullable=False)
    email = Column(LONGTEXT)
    username = Column(LONGTEXT, nullable=False)


class MOauth2UserFieldMapping(Base):
    __tablename__ = 'm_oauth2_user_field_mapping'
    __table_args__ = (
        Index('m_oautuserfielmapp_issint_uix', 'issuerid', 'internalfield', unique=True),
        {'comment': 'Mapping of oauth user fields to moodle fields.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    timemodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False)
    issuerid = Column(BIGINT(10), nullable=False, index=True)
    externalfield = Column(String(500, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    internalfield = Column(String(64, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MPage(Base):
    __tablename__ = 'm_page'
    __table_args__ = {'comment': 'Each record is one page and its config data'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    content = Column(LONGTEXT)
    contentformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    legacyfiles = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    legacyfileslast = Column(BIGINT(10))
    display = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    displayoptions = Column(LONGTEXT)
    revision = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MPaygwPaypal(Base):
    __tablename__ = 'm_paygw_paypal'
    __table_args__ = {'comment': 'Stores PayPal related information'}

    id = Column(BIGINT(10), primary_key=True)
    paymentid = Column(BIGINT(10), nullable=False, unique=True)
    pp_orderid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'The ID of the order in PayPal'"))


class MPaymentAccount(Base):
    __tablename__ = 'm_payment_accounts'
    __table_args__ = {'comment': 'Payment accounts'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    idnumber = Column(String(100, 'utf8mb4_bin'))
    contextid = Column(BIGINT(10), nullable=False)
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    archived = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10))
    timemodified = Column(BIGINT(10))


class MPaymentGateway(Base):
    __tablename__ = 'm_payment_gateways'
    __table_args__ = {'comment': 'Configuration for one gateway for one payment account'}

    id = Column(BIGINT(10), primary_key=True)
    accountid = Column(BIGINT(10), nullable=False, index=True)
    gateway = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    config = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MPayment(Base):
    __tablename__ = 'm_payments'
    __table_args__ = (
        Index('m_paym_compayite_ix', 'component', 'paymentarea', 'itemid'),
        {'comment': 'Stores information about payments'}
    )

    id = Column(BIGINT(10), primary_key=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    paymentarea = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    amount = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    currency = Column(String(3, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    accountid = Column(BIGINT(10), nullable=False, index=True)
    gateway = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MPortfolioInstance(Base):
    __tablename__ = 'm_portfolio_instance'
    __table_args__ = {'comment': 'base table (not including config data) for instances of port'}

    id = Column(BIGINT(10), primary_key=True)
    plugin = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    visible = Column(TINYINT(1), nullable=False, server_default=text("'1'"))


class MPortfolioInstanceConfig(Base):
    __tablename__ = 'm_portfolio_instance_config'
    __table_args__ = {'comment': 'config for portfolio plugin instances'}

    id = Column(BIGINT(10), primary_key=True)
    instance = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    value = Column(LONGTEXT)


class MPortfolioInstanceUser(Base):
    __tablename__ = 'm_portfolio_instance_user'
    __table_args__ = {'comment': 'user data for portfolio instances.'}

    id = Column(BIGINT(10), primary_key=True)
    instance = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT)


class MPortfolioLog(Base):
    __tablename__ = 'm_portfolio_log'
    __table_args__ = {'comment': 'log of portfolio transfers (used to later check for duplicat'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    time = Column(BIGINT(10), nullable=False)
    portfolio = Column(BIGINT(10), nullable=False, index=True)
    caller_class = Column(String(150, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    caller_file = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    caller_component = Column(String(255, 'utf8mb4_bin'))
    caller_sha1 = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    tempdataid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    returnurl = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    continueurl = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MPortfolioMaharaQueue(Base):
    __tablename__ = 'm_portfolio_mahara_queue'
    __table_args__ = {'comment': 'maps mahara tokens to transfer ids'}

    id = Column(BIGINT(10), primary_key=True)
    transferid = Column(BIGINT(10), nullable=False, index=True)
    token = Column(String(50, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))


class MPortfolioTempdatum(Base):
    __tablename__ = 'm_portfolio_tempdata'
    __table_args__ = {'comment': 'stores temporary data for portfolio exports. the id of this '}

    id = Column(BIGINT(10), primary_key=True)
    data = Column(LONGTEXT)
    expirytime = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    instance = Column(BIGINT(10), index=True, server_default=text("'0'"))
    queued = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MPost(Base):
    __tablename__ = 'm_post'
    __table_args__ = (
        Index('m_post_iduse_uix', 'id', 'userid', unique=True),
        {'comment': 'Generic post table to hold data blog entries etc in differen'}
    )

    id = Column(BIGINT(10), primary_key=True)
    module = Column(String(20, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    moduleid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    coursemoduleid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    subject = Column(String(128, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    summary = Column(LONGTEXT)
    content = Column(LONGTEXT)
    uniquehash = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    rating = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    format = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    summaryformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    attachment = Column(String(100, 'utf8mb4_bin'))
    publishstate = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'draft'"))
    lastmodified = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    created = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    usermodified = Column(BIGINT(10), index=True)


class MProfiling(Base):
    __tablename__ = 'm_profiling'
    __table_args__ = (
        Index('m_prof_timrun_ix', 'timecreated', 'runreference'),
        Index('m_prof_urlrun_ix', 'url', 'runreference'),
        {'comment': 'Stores the results of all the profiling runs'}
    )

    id = Column(BIGINT(10), primary_key=True)
    runid = Column(String(32, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    url = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    data = Column(LONGTEXT, nullable=False)
    totalexecutiontime = Column(BIGINT(10), nullable=False)
    totalcputime = Column(BIGINT(10), nullable=False)
    totalcalls = Column(BIGINT(10), nullable=False)
    totalmemory = Column(BIGINT(10), nullable=False)
    runreference = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    runcomment = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)


class MQtypeDdimageortext(Base):
    __tablename__ = 'm_qtype_ddimageortext'
    __table_args__ = {'comment': 'Defines drag and drop (text or images onto a background imag'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    correctfeedback = Column(LONGTEXT, nullable=False)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT, nullable=False)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT, nullable=False)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQtypeDdimageortextDrag(Base):
    __tablename__ = 'm_qtype_ddimageortext_drags'
    __table_args__ = {'comment': 'Images to drag. Actual file names are not stored here we use'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    no = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    draggroup = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    infinite = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    label = Column(LONGTEXT, nullable=False)


class MQtypeDdimageortextDrop(Base):
    __tablename__ = 'm_qtype_ddimageortext_drops'
    __table_args__ = {'comment': 'Drop boxes'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    no = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    xleft = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    ytop = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    choice = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    label = Column(LONGTEXT, nullable=False)


class MQtypeDdmarker(Base):
    __tablename__ = 'm_qtype_ddmarker'
    __table_args__ = {'comment': 'Defines drag and drop (text or images onto a background imag'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    correctfeedback = Column(LONGTEXT, nullable=False)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT, nullable=False)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT, nullable=False)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    showmisplaced = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))


class MQtypeDdmarkerDrag(Base):
    __tablename__ = 'm_qtype_ddmarker_drags'
    __table_args__ = {'comment': 'Labels for markers to drag.'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    no = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    label = Column(LONGTEXT, nullable=False)
    infinite = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    noofdrags = Column(BIGINT(10), nullable=False, server_default=text("'1'"))


class MQtypeDdmarkerDrop(Base):
    __tablename__ = 'm_qtype_ddmarker_drops'
    __table_args__ = {'comment': 'drop regions'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    no = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    shape = Column(String(255, 'utf8mb4_bin'))
    coords = Column(LONGTEXT, nullable=False)
    choice = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MQtypeEssayOption(Base):
    __tablename__ = 'm_qtype_essay_options'
    __table_args__ = {'comment': 'Extra options for essay questions.'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, unique=True)
    responseformat = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("'editor'"))
    responserequired = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    responsefieldlines = Column(SMALLINT(4), nullable=False, server_default=text("'15'"))
    minwordlimit = Column(BIGINT(10))
    maxwordlimit = Column(BIGINT(10))
    attachments = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    attachmentsrequired = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    graderinfo = Column(LONGTEXT)
    graderinfoformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    responsetemplate = Column(LONGTEXT)
    responsetemplateformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    maxbytes = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    filetypeslist = Column(LONGTEXT)


class MQtypeMatchOption(Base):
    __tablename__ = 'm_qtype_match_options'
    __table_args__ = {'comment': 'Defines the question-type specific options for matching ques'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, unique=True, server_default=text("'0'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    correctfeedback = Column(LONGTEXT, nullable=False)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT, nullable=False)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT, nullable=False)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQtypeMatchSubquestion(Base):
    __tablename__ = 'm_qtype_match_subquestions'
    __table_args__ = {'comment': 'The subquestions that make up a matching question'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    questiontext = Column(LONGTEXT, nullable=False)
    questiontextformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    answertext = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MQtypeMultichoiceOption(Base):
    __tablename__ = 'm_qtype_multichoice_options'
    __table_args__ = {'comment': 'Options for multiple choice questions'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, unique=True, server_default=text("'0'"))
    layout = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    single = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    correctfeedback = Column(LONGTEXT, nullable=False)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT, nullable=False)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT, nullable=False)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    answernumbering = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("'abc'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    showstandardinstruction = Column(TINYINT(2), nullable=False, server_default=text("'1'"))


class MQtypeRandomsamatchOption(Base):
    __tablename__ = 'm_qtype_randomsamatch_options'
    __table_args__ = {'comment': 'Info about a random short-answer matching question'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, unique=True, server_default=text("'0'"))
    choose = Column(BIGINT(10), nullable=False, server_default=text("'4'"))
    subcats = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    correctfeedback = Column(LONGTEXT, nullable=False)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT, nullable=False)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT, nullable=False)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQtypeShortanswerOption(Base):
    __tablename__ = 'm_qtype_shortanswer_options'
    __table_args__ = {'comment': 'Options for short answer questions'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, unique=True, server_default=text("'0'"))
    usecase = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQuestion(Base):
    __tablename__ = 'm_question'
    __table_args__ = (
        Index('m_ques_catidn_uix', 'category', 'idnumber', unique=True),
        {'comment': 'The questions themselves'}
    )

    id = Column(BIGINT(10), primary_key=True)
    category = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    parent = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    questiontext = Column(LONGTEXT, nullable=False)
    questiontextformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    generalfeedback = Column(LONGTEXT, nullable=False)
    generalfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    defaultmark = Column(DECIMAL(12, 7), nullable=False, server_default=text("'1.0000000'"))
    penalty = Column(DECIMAL(12, 7), nullable=False, server_default=text("'0.3333333'"))
    qtype = Column(String(20, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    length = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    stamp = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    version = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    hidden = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    createdby = Column(BIGINT(10), index=True)
    modifiedby = Column(BIGINT(10), index=True)
    idnumber = Column(String(100, 'utf8mb4_bin'))


class MQuestionAnswer(Base):
    __tablename__ = 'm_question_answers'
    __table_args__ = {'comment': 'Answers, with a fractional grade (0-1) and feedback'}

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    answer = Column(LONGTEXT, nullable=False)
    answerformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    fraction = Column(DECIMAL(12, 7), nullable=False, server_default=text("'0.0000000'"))
    feedback = Column(LONGTEXT, nullable=False)
    feedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQuestionAttemptStepDatum(Base):
    __tablename__ = 'm_question_attempt_step_data'
    __table_args__ = {'comment': 'Each question_attempt_step has an associative array of the d'}

    id = Column(BIGINT(10), primary_key=True)
    attemptstepid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT)


class MQuestionAttemptStep(Base):
    __tablename__ = 'm_question_attempt_steps'
    __table_args__ = (
        Index('m_quesattestep_queseq_uix', 'questionattemptid', 'sequencenumber', unique=True),
        {'comment': 'Stores one step in in a question attempt. As well as the dat'}
    )

    id = Column(BIGINT(10), primary_key=True)
    questionattemptid = Column(BIGINT(10), nullable=False, index=True)
    sequencenumber = Column(BIGINT(10), nullable=False)
    state = Column(String(13, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    fraction = Column(DECIMAL(12, 7))
    timecreated = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), index=True)


class MQuestionAttempt(Base):
    __tablename__ = 'm_question_attempts'
    __table_args__ = (
        Index('m_quesatte_queslo_uix', 'questionusageid', 'slot', unique=True),
        {'comment': 'Each row here corresponds to an attempt at one question, as '}
    )

    id = Column(BIGINT(10), primary_key=True)
    questionusageid = Column(BIGINT(10), nullable=False, index=True)
    slot = Column(BIGINT(10), nullable=False)
    behaviour = Column(String(32, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    questionid = Column(BIGINT(10), nullable=False, index=True)
    variant = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    maxmark = Column(DECIMAL(12, 7), nullable=False)
    minfraction = Column(DECIMAL(12, 7), nullable=False)
    maxfraction = Column(DECIMAL(12, 7), nullable=False, server_default=text("'1.0000000'"))
    flagged = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    questionsummary = Column(LONGTEXT)
    rightanswer = Column(LONGTEXT)
    responsesummary = Column(LONGTEXT)
    timemodified = Column(BIGINT(10), nullable=False)


class MQuestionCalculated(Base):
    __tablename__ = 'm_question_calculated'
    __table_args__ = {'comment': 'Options for questions of type calculated'}

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    answer = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    tolerance = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'0.0'"))
    tolerancetype = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    correctanswerlength = Column(BIGINT(10), nullable=False, server_default=text("'2'"))
    correctanswerformat = Column(BIGINT(10), nullable=False, server_default=text("'2'"))


class MQuestionCalculatedOption(Base):
    __tablename__ = 'm_question_calculated_options'
    __table_args__ = {'comment': 'Options for questions of type calculated'}

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    synchronize = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    single = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    correctfeedback = Column(LONGTEXT)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    answernumbering = Column(String(10, 'utf8mb4_bin'), nullable=False, server_default=text("'abc'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQuestionCategory(Base):
    __tablename__ = 'm_question_categories'
    __table_args__ = (
        Index('m_quescate_consta_uix', 'contextid', 'stamp', unique=True),
        Index('m_quescate_conidn_uix', 'contextid', 'idnumber', unique=True),
        {'comment': 'Categories are for grouping questions'}
    )

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contextid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    info = Column(LONGTEXT, nullable=False)
    infoformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    stamp = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    parent = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'999'"))
    idnumber = Column(String(100, 'utf8mb4_bin'))


class MQuestionDatasetDefinition(Base):
    __tablename__ = 'm_question_dataset_definitions'
    __table_args__ = {'comment': 'Organises and stores properties for dataset items'}

    id = Column(BIGINT(10), primary_key=True)
    category = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    type = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    options = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemcount = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MQuestionDatasetItem(Base):
    __tablename__ = 'm_question_dataset_items'
    __table_args__ = {'comment': 'Individual dataset items'}

    id = Column(BIGINT(10), primary_key=True)
    definition = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    itemnumber = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    value = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MQuestionDataset(Base):
    __tablename__ = 'm_question_datasets'
    __table_args__ = (
        Index('m_quesdata_quedat_ix', 'question', 'datasetdefinition'),
        {'comment': 'Many-many relation between questions and dataset definitions'}
    )

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    datasetdefinition = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MQuestionDdwto(Base):
    __tablename__ = 'm_question_ddwtos'
    __table_args__ = {'comment': 'Defines drag and drop (words into sentences) questions'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    correctfeedback = Column(LONGTEXT, nullable=False)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT, nullable=False)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT, nullable=False)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQuestionGapselect(Base):
    __tablename__ = 'm_question_gapselect'
    __table_args__ = {'comment': 'Defines select missing words questions'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    correctfeedback = Column(LONGTEXT, nullable=False)
    correctfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    partiallycorrectfeedback = Column(LONGTEXT, nullable=False)
    partiallycorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    incorrectfeedback = Column(LONGTEXT, nullable=False)
    incorrectfeedbackformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    shownumcorrect = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MQuestionHint(Base):
    __tablename__ = 'm_question_hints'
    __table_args__ = {'comment': 'Stores the the part of the question definition that gives di'}

    id = Column(BIGINT(10), primary_key=True)
    questionid = Column(BIGINT(10), nullable=False, index=True)
    hint = Column(LONGTEXT, nullable=False)
    hintformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    shownumcorrect = Column(TINYINT(1))
    clearwrong = Column(TINYINT(1))
    options = Column(String(255, 'utf8mb4_bin'))


class MQuestionMultianswer(Base):
    __tablename__ = 'm_question_multianswer'
    __table_args__ = {'comment': 'Options for multianswer questions'}

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    sequence = Column(LONGTEXT, nullable=False)


class MQuestionNumerical(Base):
    __tablename__ = 'm_question_numerical'
    __table_args__ = {'comment': 'Options for numerical questions.'}

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    answer = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    tolerance = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'0.0'"))


class MQuestionNumericalOption(Base):
    __tablename__ = 'm_question_numerical_options'
    __table_args__ = {'comment': 'Options for questions of type numerical This table is also u'}

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    showunits = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    unitsleft = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    unitgradingtype = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    unitpenalty = Column(DECIMAL(12, 7), nullable=False, server_default=text("'0.1000000'"))


class MQuestionNumericalUnit(Base):
    __tablename__ = 'm_question_numerical_units'
    __table_args__ = (
        Index('m_quesnumeunit_queuni_uix', 'question', 'unit', unique=True),
        {'comment': 'Optional unit options for numerical questions. This table is'}
    )

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    multiplier = Column(DECIMAL(38, 19), nullable=False, server_default=text("'1.0000000000000000000'"))
    unit = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MQuestionResponseAnalysi(Base):
    __tablename__ = 'm_question_response_analysis'
    __table_args__ = {'comment': 'Analysis of student responses given to questions.'}

    id = Column(BIGINT(10), primary_key=True)
    hashcode = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    whichtries = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timemodified = Column(BIGINT(10), nullable=False)
    questionid = Column(BIGINT(10), nullable=False)
    variant = Column(BIGINT(10))
    subqid = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    aid = Column(String(100, 'utf8mb4_bin'))
    response = Column(LONGTEXT)
    credit = Column(DECIMAL(15, 5), nullable=False)


class MQuestionResponseCount(Base):
    __tablename__ = 'm_question_response_count'
    __table_args__ = {'comment': 'Count for each responses for each try at a question.'}

    id = Column(BIGINT(10), primary_key=True)
    analysisid = Column(BIGINT(10), nullable=False, index=True)
    _try = Column('try', BIGINT(10), nullable=False)
    rcount = Column(BIGINT(10), nullable=False)


class MQuestionStatistic(Base):
    __tablename__ = 'm_question_statistics'
    __table_args__ = {'comment': 'Statistics for individual questions used in an activity.'}

    id = Column(BIGINT(10), primary_key=True)
    hashcode = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timemodified = Column(BIGINT(10), nullable=False)
    questionid = Column(BIGINT(10), nullable=False)
    slot = Column(BIGINT(10))
    subquestion = Column(SMALLINT(4), nullable=False)
    variant = Column(BIGINT(10))
    s = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    effectiveweight = Column(DECIMAL(15, 5))
    negcovar = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    discriminationindex = Column(DECIMAL(15, 5))
    discriminativeefficiency = Column(DECIMAL(15, 5))
    sd = Column(DECIMAL(15, 10))
    facility = Column(DECIMAL(15, 10))
    subquestions = Column(LONGTEXT)
    maxmark = Column(DECIMAL(12, 7))
    positions = Column(LONGTEXT)
    randomguessscore = Column(DECIMAL(12, 7))


class MQuestionTruefalse(Base):
    __tablename__ = 'm_question_truefalse'
    __table_args__ = {'comment': 'Options for True-False questions'}

    id = Column(BIGINT(10), primary_key=True)
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    trueanswer = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    falseanswer = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MQuestionUsage(Base):
    __tablename__ = 'm_question_usages'
    __table_args__ = {'comment': "This table's main purpose it to assign a unique id to each a"}

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    component = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    preferredbehaviour = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MQuiz(Base):
    __tablename__ = 'm_quiz'
    __table_args__ = {'comment': 'The settings for each quiz.'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    timeopen = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeclose = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timelimit = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    overduehandling = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("'autoabandon'"))
    graceperiod = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    preferredbehaviour = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    canredoquestions = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    attempts = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    attemptonlast = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    grademethod = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    decimalpoints = Column(SMALLINT(4), nullable=False, server_default=text("'2'"))
    questiondecimalpoints = Column(SMALLINT(4), nullable=False, server_default=text("'-1'"))
    reviewattempt = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    reviewcorrectness = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    reviewmarks = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    reviewspecificfeedback = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    reviewgeneralfeedback = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    reviewrightanswer = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    reviewoverallfeedback = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    questionsperpage = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    navmethod = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("'free'"))
    shuffleanswers = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    sumgrades = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    grade = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    password = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    subnet = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    browsersecurity = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    delay1 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    delay2 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    showuserpicture = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    showblocks = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    completionattemptsexhausted = Column(TINYINT(1), server_default=text("'0'"))
    completionpass = Column(TINYINT(1), server_default=text("'0'"))
    completionminattempts = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    allowofflineattempts = Column(TINYINT(1), server_default=text("'0'"))


class MQuizAttempt(Base):
    __tablename__ = 'm_quiz_attempts'
    __table_args__ = (
        Index('m_quizatte_statim_ix', 'state', 'timecheckstate'),
        Index('m_quizatte_quiuseatt_uix', 'quiz', 'userid', 'attempt', unique=True),
        {'comment': 'Stores users attempts at quizzes.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    quiz = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    attempt = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    uniqueid = Column(BIGINT(10), nullable=False, unique=True, server_default=text("'0'"))
    layout = Column(LONGTEXT, nullable=False)
    currentpage = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    preview = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    state = Column(String(16, 'utf8mb4_bin'), nullable=False, server_default=text("'inprogress'"))
    timestart = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timefinish = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodifiedoffline = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timecheckstate = Column(BIGINT(10), server_default=text("'0'"))
    sumgrades = Column(DECIMAL(10, 5))


class MQuizFeedback(Base):
    __tablename__ = 'm_quiz_feedback'
    __table_args__ = {'comment': 'Feedback given to students based on which grade band their o'}

    id = Column(BIGINT(10), primary_key=True)
    quizid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    feedbacktext = Column(LONGTEXT, nullable=False)
    feedbacktextformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    mingrade = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    maxgrade = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))


class MQuizGrade(Base):
    __tablename__ = 'm_quiz_grades'
    __table_args__ = {'comment': 'Stores the overall grade for each user on the quiz, based on'}

    id = Column(BIGINT(10), primary_key=True)
    quiz = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    grade = Column(DECIMAL(10, 5), nullable=False, server_default=text("'0.00000'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MQuizOverride(Base):
    __tablename__ = 'm_quiz_overrides'
    __table_args__ = {'comment': 'The overrides to quiz settings on a per-user and per-group b'}

    id = Column(BIGINT(10), primary_key=True)
    quiz = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), index=True)
    userid = Column(BIGINT(10), index=True)
    timeopen = Column(BIGINT(10))
    timeclose = Column(BIGINT(10))
    timelimit = Column(BIGINT(10))
    attempts = Column(MEDIUMINT(6))
    password = Column(String(255, 'utf8mb4_bin'))


class MQuizOverviewRegrade(Base):
    __tablename__ = 'm_quiz_overview_regrades'
    __table_args__ = (
        Index('m_quizoverregr_queslo_ix', 'questionusageid', 'slot'),
        {'comment': 'This table records which question attempts need regrading an'}
    )

    id = Column(BIGINT(10), primary_key=True)
    questionusageid = Column(BIGINT(10), nullable=False)
    slot = Column(BIGINT(10), nullable=False)
    newfraction = Column(DECIMAL(12, 7))
    oldfraction = Column(DECIMAL(12, 7))
    regraded = Column(SMALLINT(4), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MQuizReport(Base):
    __tablename__ = 'm_quiz_reports'
    __table_args__ = {'comment': 'Lists all the installed quiz reports and their display order'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), unique=True)
    displayorder = Column(BIGINT(10), nullable=False)
    capability = Column(String(255, 'utf8mb4_bin'))


class MQuizSection(Base):
    __tablename__ = 'm_quiz_sections'
    __table_args__ = (
        Index('m_quizsect_quifir_uix', 'quizid', 'firstslot', unique=True),
        {'comment': 'Stores sections of a quiz with section name (heading), from '}
    )

    id = Column(BIGINT(10), primary_key=True)
    quizid = Column(BIGINT(10), nullable=False, index=True)
    firstslot = Column(BIGINT(10), nullable=False)
    heading = Column(String(1333, 'utf8mb4_bin'))
    shufflequestions = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))


class MQuizSlotTag(Base):
    __tablename__ = 'm_quiz_slot_tags'
    __table_args__ = {'comment': 'Stores data about the tags that a question must have so that'}

    id = Column(BIGINT(10), primary_key=True)
    slotid = Column(BIGINT(10), index=True)
    tagid = Column(BIGINT(10), index=True)
    tagname = Column(String(255, 'utf8mb4_bin'))


class MQuizSlot(Base):
    __tablename__ = 'm_quiz_slots'
    __table_args__ = (
        Index('m_quizslot_quislo_uix', 'quizid', 'slot', unique=True),
        {'comment': 'Stores the question used in a quiz, with the order, and for '}
    )

    id = Column(BIGINT(10), primary_key=True)
    slot = Column(BIGINT(10), nullable=False)
    quizid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    page = Column(BIGINT(10), nullable=False)
    requireprevious = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    questionid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    questioncategoryid = Column(BIGINT(10), index=True)
    includingsubcategories = Column(SMALLINT(4))
    maxmark = Column(DECIMAL(12, 7), nullable=False, server_default=text("'0.0000000'"))


class MQuizStatistic(Base):
    __tablename__ = 'm_quiz_statistics'
    __table_args__ = {'comment': 'table to cache results from analysis done in statistics repo'}

    id = Column(BIGINT(10), primary_key=True)
    hashcode = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    whichattempts = Column(SMALLINT(4), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    firstattemptscount = Column(BIGINT(10), nullable=False)
    highestattemptscount = Column(BIGINT(10), nullable=False)
    lastattemptscount = Column(BIGINT(10), nullable=False)
    allattemptscount = Column(BIGINT(10), nullable=False)
    firstattemptsavg = Column(DECIMAL(15, 5))
    highestattemptsavg = Column(DECIMAL(15, 5))
    lastattemptsavg = Column(DECIMAL(15, 5))
    allattemptsavg = Column(DECIMAL(15, 5))
    median = Column(DECIMAL(15, 5))
    standarddeviation = Column(DECIMAL(15, 5))
    skewness = Column(DECIMAL(15, 10))
    kurtosis = Column(DECIMAL(15, 5))
    cic = Column(DECIMAL(15, 10))
    errorratio = Column(DECIMAL(15, 10))
    standarderror = Column(DECIMAL(15, 10))


class MQuizaccessSebQuizsetting(Base):
    __tablename__ = 'm_quizaccess_seb_quizsettings'
    __table_args__ = {'comment': 'Stores the quiz level Safe Exam Browser configuration.'}

    id = Column(BIGINT(10), primary_key=True)
    quizid = Column(BIGINT(10), nullable=False, unique=True)
    cmid = Column(BIGINT(10), nullable=False, unique=True)
    templateid = Column(BIGINT(10), nullable=False, index=True)
    requiresafeexambrowser = Column(TINYINT(1), nullable=False)
    showsebtaskbar = Column(TINYINT(1))
    showwificontrol = Column(TINYINT(1))
    showreloadbutton = Column(TINYINT(1))
    showtime = Column(TINYINT(1))
    showkeyboardlayout = Column(TINYINT(1))
    allowuserquitseb = Column(TINYINT(1))
    quitpassword = Column(LONGTEXT)
    linkquitseb = Column(LONGTEXT)
    userconfirmquit = Column(TINYINT(1))
    enableaudiocontrol = Column(TINYINT(1))
    muteonstartup = Column(TINYINT(1))
    allowspellchecking = Column(TINYINT(1))
    allowreloadinexam = Column(TINYINT(1))
    activateurlfiltering = Column(TINYINT(1))
    filterembeddedcontent = Column(TINYINT(1))
    expressionsallowed = Column(LONGTEXT)
    regexallowed = Column(LONGTEXT)
    expressionsblocked = Column(LONGTEXT)
    regexblocked = Column(LONGTEXT)
    allowedbrowserexamkeys = Column(LONGTEXT)
    showsebdownloadlink = Column(TINYINT(1))
    usermodified = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MQuizaccessSebTemplate(Base):
    __tablename__ = 'm_quizaccess_seb_template'
    __table_args__ = {'comment': 'Templates for Safe Exam Browser configuration.'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT, nullable=False)
    content = Column(LONGTEXT, nullable=False)
    enabled = Column(TINYINT(1), nullable=False)
    sortorder = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MRating(Base):
    __tablename__ = 'm_rating'
    __table_args__ = (
        Index('m_rati_comratconite_ix', 'component', 'ratingarea', 'contextid', 'itemid'),
        {'comment': 'moodle ratings'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    ratingarea = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    scaleid = Column(BIGINT(10), nullable=False)
    rating = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MRegistrationHub(Base):
    __tablename__ = 'm_registration_hubs'
    __table_args__ = {'comment': 'hub where the site is registered on with their associated to'}

    id = Column(BIGINT(10), primary_key=True)
    token = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    hubname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    huburl = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    confirmed = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    secret = Column(String(255, 'utf8mb4_bin'))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MRepository(Base):
    __tablename__ = 'm_repository'
    __table_args__ = {'comment': 'This table contains one entry for every configured external '}

    id = Column(BIGINT(10), primary_key=True)
    type = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    visible = Column(TINYINT(1), server_default=text("'1'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MRepositoryInstanceConfig(Base):
    __tablename__ = 'm_repository_instance_config'
    __table_args__ = {'comment': 'The config for intances'}

    id = Column(BIGINT(10), primary_key=True)
    instanceid = Column(BIGINT(10), nullable=False)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT)


class MRepositoryInstance(Base):
    __tablename__ = 'm_repository_instances'
    __table_args__ = {'comment': 'This table contains one entry for every configured external '}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    typeid = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    contextid = Column(BIGINT(10), nullable=False)
    username = Column(String(255, 'utf8mb4_bin'))
    password = Column(String(255, 'utf8mb4_bin'))
    timecreated = Column(BIGINT(10))
    timemodified = Column(BIGINT(10))
    readonly = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MRepositoryOnedriveAcces(Base):
    __tablename__ = 'm_repository_onedrive_access'
    __table_args__ = {'comment': 'List of temporary access grants.'}

    id = Column(BIGINT(10), primary_key=True)
    timemodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10), nullable=False, index=True)
    permissionid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MResource(Base):
    __tablename__ = 'm_resource'
    __table_args__ = {'comment': 'Each record is one resource and its config data'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    tobemigrated = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    legacyfiles = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    legacyfileslast = Column(BIGINT(10))
    display = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    displayoptions = Column(LONGTEXT)
    filterfiles = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    revision = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MResourceOld(Base):
    __tablename__ = 'm_resource_old'
    __table_args__ = {'comment': 'backup of all old resource instances from 1.9'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    type = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    reference = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    alltext = Column(LONGTEXT, nullable=False)
    popup = Column(LONGTEXT, nullable=False)
    options = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    oldid = Column(BIGINT(10), nullable=False, unique=True)
    cmid = Column(BIGINT(10), index=True)
    newmodule = Column(String(50, 'utf8mb4_bin'))
    newid = Column(BIGINT(10))
    migrated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MRole(Base):
    __tablename__ = 'm_role'
    __table_args__ = {'comment': 'moodle roles'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    shortname = Column(String(100, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    description = Column(LONGTEXT, nullable=False)
    sortorder = Column(BIGINT(10), nullable=False, unique=True, server_default=text("'0'"))
    archetype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MRoleAllowAssign(Base):
    __tablename__ = 'm_role_allow_assign'
    __table_args__ = (
        Index('m_rolealloassi_rolall_uix', 'roleid', 'allowassign', unique=True),
        {'comment': 'this defines what role can assign what role'}
    )

    id = Column(BIGINT(10), primary_key=True)
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    allowassign = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MRoleAllowOverride(Base):
    __tablename__ = 'm_role_allow_override'
    __table_args__ = (
        Index('m_rolealloover_rolall_uix', 'roleid', 'allowoverride', unique=True),
        {'comment': 'this defines what role can override what role'}
    )

    id = Column(BIGINT(10), primary_key=True)
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    allowoverride = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MRoleAllowSwitch(Base):
    __tablename__ = 'm_role_allow_switch'
    __table_args__ = (
        Index('m_rolealloswit_rolall_uix', 'roleid', 'allowswitch', unique=True),
        {'comment': 'This table stores which which other roles a user is allowed '}
    )

    id = Column(BIGINT(10), primary_key=True)
    roleid = Column(BIGINT(10), nullable=False, index=True)
    allowswitch = Column(BIGINT(10), nullable=False, index=True)


class MRoleAllowView(Base):
    __tablename__ = 'm_role_allow_view'
    __table_args__ = (
        Index('m_rolealloview_rolall_uix', 'roleid', 'allowview', unique=True),
        {'comment': 'This table stores which which other roles a user is allowed '}
    )

    id = Column(BIGINT(10), primary_key=True)
    roleid = Column(BIGINT(10), nullable=False, index=True)
    allowview = Column(BIGINT(10), nullable=False, index=True)


class MRoleAssignment(Base):
    __tablename__ = 'm_role_assignments'
    __table_args__ = (
        Index('m_roleassi_comiteuse_ix', 'component', 'itemid', 'userid'),
        Index('m_roleassi_useconrol_ix', 'userid', 'contextid', 'roleid'),
        Index('m_roleassi_rolcon_ix', 'roleid', 'contextid'),
        {'comment': 'assigning roles in different context'}
    )

    id = Column(BIGINT(10), primary_key=True)
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    contextid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    modifierid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    sortorder = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MRoleCapability(Base):
    __tablename__ = 'm_role_capabilities'
    __table_args__ = (
        Index('m_rolecapa_rolconcap_uix', 'roleid', 'contextid', 'capability', unique=True),
        {'comment': 'permission has to be signed, overriding a capability for a p'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    capability = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    permission = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    modifierid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MRoleContextLevel(Base):
    __tablename__ = 'm_role_context_levels'
    __table_args__ = (
        Index('m_rolecontleve_conrol_uix', 'contextlevel', 'roleid', unique=True),
        {'comment': 'Lists which roles can be assigned at which context levels. T'}
    )

    id = Column(BIGINT(10), primary_key=True)
    roleid = Column(BIGINT(10), nullable=False, index=True)
    contextlevel = Column(BIGINT(10), nullable=False)


class MRoleName(Base):
    __tablename__ = 'm_role_names'
    __table_args__ = (
        Index('m_rolename_rolcon_uix', 'roleid', 'contextid', unique=True),
        {'comment': 'role names in native strings'}
    )

    id = Column(BIGINT(10), primary_key=True)
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    contextid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MScale(Base):
    __tablename__ = 'm_scale'
    __table_args__ = {'comment': 'Defines grading scales'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    scale = Column(LONGTEXT, nullable=False)
    description = Column(LONGTEXT, nullable=False)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MScaleHistory(Base):
    __tablename__ = 'm_scale_history'
    __table_args__ = {'comment': 'History table'}

    id = Column(BIGINT(10), primary_key=True)
    action = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    oldid = Column(BIGINT(10), nullable=False, index=True)
    source = Column(String(255, 'utf8mb4_bin'))
    timemodified = Column(BIGINT(10), index=True)
    loggeduser = Column(BIGINT(10), index=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    scale = Column(LONGTEXT, nullable=False)
    description = Column(LONGTEXT, nullable=False)


class MScorm(Base):
    __tablename__ = 'm_scorm'
    __table_args__ = {'comment': 'each table is one SCORM module and its configuration'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    scormtype = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("'local'"))
    reference = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    version = Column(String(9, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    maxgrade = Column(Float(asdecimal=True), nullable=False, server_default=text("'0'"))
    grademethod = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    whatgrade = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    maxattempt = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    forcecompleted = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    forcenewattempt = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    lastattemptlock = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    masteryoverride = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    displayattemptstatus = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    displaycoursestructure = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    updatefreq = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    sha1hash = Column(String(40, 'utf8mb4_bin'))
    md5hash = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    revision = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    launch = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    skipview = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    hidebrowse = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    hidetoc = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    nav = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    navpositionleft = Column(BIGINT(10), server_default=text("'-100'"))
    navpositiontop = Column(BIGINT(10), server_default=text("'-100'"))
    auto = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    popup = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    options = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    width = Column(BIGINT(10), nullable=False, server_default=text("'100'"))
    height = Column(BIGINT(10), nullable=False, server_default=text("'600'"))
    timeopen = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeclose = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    completionstatusrequired = Column(TINYINT(1))
    completionscorerequired = Column(BIGINT(10))
    completionstatusallscos = Column(TINYINT(1))
    displayactivityname = Column(SMALLINT(4), nullable=False, server_default=text("'1'"))
    autocommit = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MScormAiccSession(Base):
    __tablename__ = 'm_scorm_aicc_session'
    __table_args__ = {'comment': 'Used by AICC HACP to store session information'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    scormid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    hacpsession = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    scoid = Column(BIGINT(10), server_default=text("'0'"))
    scormmode = Column(String(50, 'utf8mb4_bin'))
    scormstatus = Column(String(255, 'utf8mb4_bin'))
    attempt = Column(BIGINT(10))
    lessonstatus = Column(String(255, 'utf8mb4_bin'))
    sessiontime = Column(String(255, 'utf8mb4_bin'))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MScormSco(Base):
    __tablename__ = 'm_scorm_scoes'
    __table_args__ = {'comment': 'each SCO part of the SCORM module'}

    id = Column(BIGINT(10), primary_key=True)
    scorm = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    manifest = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    organization = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    parent = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    identifier = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    launch = Column(LONGTEXT, nullable=False)
    scormtype = Column(String(5, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    title = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MScormScoesDatum(Base):
    __tablename__ = 'm_scorm_scoes_data'
    __table_args__ = {'comment': 'Contains variable data get from packages'}

    id = Column(BIGINT(10), primary_key=True)
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT, nullable=False)


class MScormScoesTrack(Base):
    __tablename__ = 'm_scorm_scoes_track'
    __table_args__ = (
        Index('m_scorscoetrac_usescoscoat_uix', 'userid', 'scormid', 'scoid', 'attempt', 'element', unique=True),
        {'comment': 'to track SCOes'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    scormid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    attempt = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    element = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(LONGTEXT, nullable=False)
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MScormSeqMapinfo(Base):
    __tablename__ = 'm_scorm_seq_mapinfo'
    __table_args__ = (
        Index('m_scorseqmapi_scoidobj_uix', 'scoid', 'id', 'objectiveid', unique=True),
        {'comment': 'SCORM2004 objective mapinfo description'}
    )

    id = Column(BIGINT(10), primary_key=True)
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    objectiveid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    targetobjectiveid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    readsatisfiedstatus = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    readnormalizedmeasure = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    writesatisfiedstatus = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    writenormalizedmeasure = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MScormSeqObjective(Base):
    __tablename__ = 'm_scorm_seq_objective'
    __table_args__ = (
        Index('m_scorseqobje_scoid_uix', 'scoid', 'id', unique=True),
        {'comment': 'SCORM2004 objective description'}
    )

    id = Column(BIGINT(10), primary_key=True)
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    primaryobj = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    objectiveid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    satisfiedbymeasure = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    minnormalizedmeasure = Column(Float(11), nullable=False, server_default=text("'0.0000'"))


class MScormSeqRolluprule(Base):
    __tablename__ = 'm_scorm_seq_rolluprule'
    __table_args__ = (
        Index('m_scorseqroll_scoid_uix', 'scoid', 'id', unique=True),
        {'comment': 'SCORM2004 sequencing rule'}
    )

    id = Column(BIGINT(10), primary_key=True)
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    childactivityset = Column(String(15, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    minimumcount = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    minimumpercent = Column(Float(11), nullable=False, server_default=text("'0.0000'"))
    conditioncombination = Column(String(3, 'utf8mb4_bin'), nullable=False, server_default=text("'all'"))
    action = Column(String(15, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MScormSeqRolluprulecond(Base):
    __tablename__ = 'm_scorm_seq_rolluprulecond'
    __table_args__ = (
        Index('m_scorseqroll_scorolid_uix', 'scoid', 'rollupruleid', 'id', unique=True),
        {'comment': 'SCORM2004 sequencing rule'}
    )

    id = Column(BIGINT(10), primary_key=True)
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    rollupruleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    operator = Column(String(5, 'utf8mb4_bin'), nullable=False, server_default=text("'noOp'"))
    cond = Column(String(25, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MScormSeqRulecond(Base):
    __tablename__ = 'm_scorm_seq_rulecond'
    __table_args__ = (
        Index('m_scorseqrule_idscorul_uix', 'id', 'scoid', 'ruleconditionsid', unique=True),
        {'comment': 'SCORM2004 rule condition'}
    )

    id = Column(BIGINT(10), primary_key=True)
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    ruleconditionsid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    refrencedobjective = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    measurethreshold = Column(Float(11), nullable=False, server_default=text("'0.0000'"))
    operator = Column(String(5, 'utf8mb4_bin'), nullable=False, server_default=text("'noOp'"))
    cond = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("'always'"))


class MScormSeqRulecond(Base):
    __tablename__ = 'm_scorm_seq_ruleconds'
    __table_args__ = (
        Index('m_scorseqrule_scoid_uix', 'scoid', 'id', unique=True),
        {'comment': 'SCORM2004 rule conditions'}
    )

    id = Column(BIGINT(10), primary_key=True)
    scoid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    conditioncombination = Column(String(3, 'utf8mb4_bin'), nullable=False, server_default=text("'all'"))
    ruletype = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    action = Column(String(25, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MSearchIndexRequest(Base):
    __tablename__ = 'm_search_index_requests'
    __table_args__ = (
        Index('m_searinderequ_indtim_ix', 'indexpriority', 'timerequested'),
        {'comment': 'Records requests for (re)indexing of specific contexts. Entr'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, index=True)
    searcharea = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timerequested = Column(BIGINT(10), nullable=False)
    partialarea = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    partialtime = Column(BIGINT(10), nullable=False)
    indexpriority = Column(BIGINT(10), nullable=False)


class MSearchSimpledbIndex(Base):
    __tablename__ = 'm_search_simpledb_index'
    __table_args__ = (
        Index('m_searsimpinde_owncon_ix', 'owneruserid', 'contextid'),
        Index('m_search_simpledb_index_index', 'title', 'content', 'description1', 'description2'),
        {'comment': 'search_simpledb table containing the index data.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    docid = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    title = Column(LONGTEXT)
    content = Column(LONGTEXT)
    contextid = Column(BIGINT(10), nullable=False)
    areaid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    type = Column(TINYINT(1), nullable=False)
    courseid = Column(BIGINT(10), nullable=False)
    owneruserid = Column(BIGINT(10))
    modified = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10))
    description1 = Column(LONGTEXT)
    description2 = Column(LONGTEXT)


class MSession(Base):
    __tablename__ = 'm_sessions'
    __table_args__ = {'comment': 'Database based session storage - now recommended'}

    id = Column(BIGINT(10), primary_key=True)
    state = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    sid = Column(String(128, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    userid = Column(BIGINT(10), nullable=False, index=True)
    sessdata = Column(LONGTEXT)
    timecreated = Column(BIGINT(10), nullable=False, index=True)
    timemodified = Column(BIGINT(10), nullable=False, index=True)
    firstip = Column(String(45, 'utf8mb4_bin'))
    lastip = Column(String(45, 'utf8mb4_bin'))


class MStatsDaily(Base):
    __tablename__ = 'm_stats_daily'
    __table_args__ = {'comment': 'to accumulate daily stats'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    stattype = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'activity'"))
    stat1 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    stat2 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MStatsMonthly(Base):
    __tablename__ = 'm_stats_monthly'
    __table_args__ = {'comment': 'To accumulate monthly stats'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    stattype = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'activity'"))
    stat1 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    stat2 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MStatsUserDaily(Base):
    __tablename__ = 'm_stats_user_daily'
    __table_args__ = {'comment': 'To accumulate daily stats per course/user'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    statsreads = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    statswrites = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    stattype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MStatsUserMonthly(Base):
    __tablename__ = 'm_stats_user_monthly'
    __table_args__ = {'comment': 'To accumulate monthly stats per course/user'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    statsreads = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    statswrites = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    stattype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MStatsUserWeekly(Base):
    __tablename__ = 'm_stats_user_weekly'
    __table_args__ = {'comment': 'To accumulate weekly stats per course/user'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    statsreads = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    statswrites = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    stattype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MStatsWeekly(Base):
    __tablename__ = 'm_stats_weekly'
    __table_args__ = {'comment': 'To accumulate weekly stats'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    roleid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    stattype = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'activity'"))
    stat1 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    stat2 = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MSurvey(Base):
    __tablename__ = 'm_survey'
    __table_args__ = {'comment': 'Each record is one SURVEY module with its configuration'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    template = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    days = Column(MEDIUMINT(6), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT, nullable=False)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    questions = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    completionsubmit = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MSurveyAnalysi(Base):
    __tablename__ = 'm_survey_analysis'
    __table_args__ = {'comment': 'text about each survey submission'}

    id = Column(BIGINT(10), primary_key=True)
    survey = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    notes = Column(LONGTEXT, nullable=False)


class MSurveyAnswer(Base):
    __tablename__ = 'm_survey_answers'
    __table_args__ = {'comment': 'the answers to each questions filled by the users'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    survey = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    question = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    time = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    answer1 = Column(LONGTEXT, nullable=False)
    answer2 = Column(LONGTEXT, nullable=False)


class MSurveyQuestion(Base):
    __tablename__ = 'm_survey_questions'
    __table_args__ = {'comment': 'the questions conforming one survey'}

    id = Column(BIGINT(10), primary_key=True)
    text = Column(String(255, 'utf8mb4_bin'), nullable=False) # , server_default=text("''"))
    shorttext = Column(String(30, 'utf8mb4_bin'), nullable=False) # , server_default=text("''"))
    multi = Column(String(100, 'utf8mb4_bin'), nullable=False) # , server_default=text("''"))
    intro = Column(String(50, 'utf8mb4_bin'), nullable=False) # , server_default=text("''"))
    type = Column(SMALLINT(3), nullable=False) # , server_default=text("'0'"))
    options = Column(LONGTEXT)


class MTag(Base):
    __tablename__ = 'm_tag'
    __table_args__ = (
        Index('m_tag_tagnam_uix', 'tagcollid', 'name', unique=True),
        Index('m_tag_tagiss_ix', 'tagcollid', 'isstandard'),
        {'comment': 'Tag table - this generic table will replace the old "tags" t'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    tagcollid = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    rawname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    isstandard = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    flag = Column(SMALLINT(4), server_default=text("'0'"))
    timemodified = Column(BIGINT(10))


class MTagArea(Base):
    __tablename__ = 'm_tag_area'
    __table_args__ = (
        Index('m_tagarea_comite_uix', 'component', 'itemtype', unique=True),
        {'comment': 'Defines various tag areas, one area is identified by compone'}
    )

    id = Column(BIGINT(10), primary_key=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemtype = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    tagcollid = Column(BIGINT(10), nullable=False, index=True)
    callback = Column(String(100, 'utf8mb4_bin'))
    callbackfile = Column(String(100, 'utf8mb4_bin'))
    showstandard = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    multiplecontexts = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MTagColl(Base):
    __tablename__ = 'm_tag_coll'
    __table_args__ = {'comment': 'Defines different set of tags'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'))
    isdefault = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    component = Column(String(100, 'utf8mb4_bin'))
    sortorder = Column(MEDIUMINT(5), nullable=False, server_default=text("'0'"))
    searchable = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    customurl = Column(String(255, 'utf8mb4_bin'))


class MTagCorrelation(Base):
    __tablename__ = 'm_tag_correlation'
    __table_args__ = {'comment': "The rationale for the 'tag_correlation' table is performance"}

    id = Column(BIGINT(10), primary_key=True)
    tagid = Column(BIGINT(10), nullable=False, index=True)
    correlatedtags = Column(LONGTEXT, nullable=False)


class MTagInstance(Base):
    __tablename__ = 'm_tag_instance'
    __table_args__ = (
        Index('m_taginst_comiteitecontiut_uix', 'component', 'itemtype', 'itemid', 'contextid', 'tiuserid', 'tagid', unique=True),
        Index('m_taginst_itecomtagcon_ix', 'itemtype', 'component', 'tagid', 'contextid'),
        {'comment': 'tag_instance table holds the information of associations bet'}
    )

    id = Column(BIGINT(10), primary_key=True)
    tagid = Column(BIGINT(10), nullable=False, index=True)
    component = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemtype = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    itemid = Column(BIGINT(10), nullable=False)
    contextid = Column(BIGINT(10), index=True)
    tiuserid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    ordering = Column(BIGINT(10))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MTaskAdhoc(Base):
    __tablename__ = 'm_task_adhoc'
    __table_args__ = {'comment': 'List of adhoc tasks waiting to run.'}

    id = Column(BIGINT(10), primary_key=True)
    component = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    classname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    nextruntime = Column(BIGINT(10), nullable=False, index=True)
    faildelay = Column(BIGINT(10))
    customdata = Column(LONGTEXT)
    userid = Column(BIGINT(10), index=True)
    blocking = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timestarted = Column(BIGINT(10))
    hostname = Column(String(255, 'utf8mb4_bin'))
    pid = Column(BIGINT(10))


class MTaskLog(Base):
    __tablename__ = 'm_task_log'
    __table_args__ = {'comment': 'The log table for all tasks'}

    id = Column(BIGINT(10), primary_key=True)
    type = Column(SMALLINT(4), nullable=False)
    component = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    classname = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    userid = Column(BIGINT(10), nullable=False)
    timestart = Column(DECIMAL(20, 10), nullable=False, index=True)
    timeend = Column(DECIMAL(20, 10), nullable=False)
    dbreads = Column(BIGINT(10), nullable=False)
    dbwrites = Column(BIGINT(10), nullable=False)
    result = Column(TINYINT(2), nullable=False)
    output = Column(LONGTEXT, nullable=False)
    hostname = Column(String(255, 'utf8mb4_bin'))
    pid = Column(BIGINT(10))


class MTaskScheduled(Base):
    __tablename__ = 'm_task_scheduled'
    __table_args__ = {'comment': 'List of scheduled tasks to be run by cron.'}

    id = Column(BIGINT(10), primary_key=True)
    component = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    classname = Column(String(255, 'utf8mb4_bin'), nullable=False, unique=True, server_default=text("''"))
    lastruntime = Column(BIGINT(10))
    nextruntime = Column(BIGINT(10))
    blocking = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    minute = Column(String(25, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    hour = Column(String(25, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    day = Column(String(25, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    month = Column(String(25, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    dayofweek = Column(String(25, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    faildelay = Column(BIGINT(10))
    customised = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    disabled = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timestarted = Column(BIGINT(10))
    hostname = Column(String(255, 'utf8mb4_bin'))
    pid = Column(BIGINT(10))


class MToolBrickfieldArea(Base):
    __tablename__ = 'm_tool_brickfield_areas'
    __table_args__ = (
        Index('m_toolbricarea_typtabitefie_ix', 'type', 'tablename', 'itemid', 'fieldorarea'),
        Index('m_toolbricarea_refreftyp_ix', 'reftable', 'refid', 'type'),
        Index('m_toolbricarea_coucmi_ix', 'courseid', 'cmid'),
        Index('m_toolbricarea_typconcomfie_ix', 'type', 'contextid', 'component', 'fieldorarea', 'itemid'),
        {'comment': 'Areas that have been checked for accessibility problems'}
    )

    id = Column(BIGINT(10), primary_key=True)
    type = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    contextid = Column(BIGINT(10), index=True)
    component = Column(String(100, 'utf8mb4_bin'))
    tablename = Column(String(40, 'utf8mb4_bin'))
    fieldorarea = Column(String(50, 'utf8mb4_bin'))
    itemid = Column(BIGINT(10))
    filename = Column(String(1333, 'utf8mb4_bin'))
    reftable = Column(String(40, 'utf8mb4_bin'))
    refid = Column(BIGINT(10))
    cmid = Column(BIGINT(10), index=True)
    courseid = Column(BIGINT(10), index=True)
    categoryid = Column(BIGINT(10), index=True)


class MToolBrickfieldCacheAct(Base):
    __tablename__ = 'm_tool_brickfield_cache_acts'
    __table_args__ = {'comment': 'Contains accessibility summary information per activity.'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    status = Column(TINYINT(1), index=True)
    component = Column(String(64, 'utf8mb4_bin'))
    totalactivities = Column(BIGINT(10))
    failedactivities = Column(BIGINT(10))
    passedactivities = Column(BIGINT(10))
    errorcount = Column(BIGINT(10))


class MToolBrickfieldCacheCheck(Base):
    __tablename__ = 'm_tool_brickfield_cache_check'
    __table_args__ = {'comment': 'Contains accessibility summary information per check.'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    status = Column(TINYINT(1), index=True)
    checkid = Column(BIGINT(10))
    checkcount = Column(BIGINT(10))
    errorcount = Column(BIGINT(10), index=True)


class MToolBrickfieldCheck(Base):
    __tablename__ = 'm_tool_brickfield_checks'
    __table_args__ = {'comment': 'Checks details'}

    id = Column(BIGINT(10), primary_key=True)
    checktype = Column(String(64, 'utf8mb4_bin'), index=True)
    shortname = Column(String(64, 'utf8mb4_bin'))
    checkgroup = Column(BIGINT(16), index=True, server_default=text("'0'"))
    status = Column(SMALLINT(4), nullable=False, index=True)
    severity = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MToolBrickfieldContent(Base):
    __tablename__ = 'm_tool_brickfield_content'
    __table_args__ = (
        Index('m_toolbriccont_iscare_ix', 'iscurrent', 'areaid'),
        {'comment': 'Content of an area at a particular time (recognised by a has'}
    )

    id = Column(BIGINT(10), primary_key=True)
    areaid = Column(BIGINT(10), nullable=False, index=True)
    contenthash = Column(String(40, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    iscurrent = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    status = Column(TINYINT(2), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False)
    timechecked = Column(BIGINT(10))


class MToolBrickfieldError(Base):
    __tablename__ = 'm_tool_brickfield_errors'
    __table_args__ = {'comment': 'Errors during the accessibility checks'}

    id = Column(BIGINT(10), primary_key=True)
    resultid = Column(BIGINT(10), nullable=False, index=True)
    linenumber = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    errordata = Column(LONGTEXT)
    htmlcode = Column(LONGTEXT)


class MToolBrickfieldProces(Base):
    __tablename__ = 'm_tool_brickfield_process'
    __table_args__ = {'comment': 'Queued records to initiate new processing of specific target'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False)
    item = Column(String(64, 'utf8mb4_bin'))
    contextid = Column(BIGINT(10))
    innercontextid = Column(BIGINT(10))
    timecreated = Column(BIGINT(16))
    timecompleted = Column(BIGINT(16), index=True)


class MToolBrickfieldResult(Base):
    __tablename__ = 'm_tool_brickfield_results'
    __table_args__ = (
        Index('m_toolbricresu_conche_ix', 'contentid', 'checkid'),
        {'comment': 'Results of the accessibility checks'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contentid = Column(BIGINT(10), index=True)
    checkid = Column(BIGINT(10), nullable=False, index=True)
    errorcount = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MToolBrickfieldSchedule(Base):
    __tablename__ = 'm_tool_brickfield_schedule'
    __table_args__ = (
        Index('m_toolbricsche_conins_uix', 'contextlevel', 'instanceid', unique=True),
        {'comment': 'Keeps the per course content analysis schedule.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    contextlevel = Column(BIGINT(10), nullable=False, server_default=text("'50'"))
    instanceid = Column(BIGINT(10), nullable=False)
    contextid = Column(BIGINT(10))
    status = Column(TINYINT(2), nullable=False, index=True, server_default=text("'0'"))
    timeanalyzed = Column(BIGINT(10), server_default=text("'0'"))
    timemodified = Column(BIGINT(10), server_default=text("'0'"))


class MToolBrickfieldSummary(Base):
    __tablename__ = 'm_tool_brickfield_summary'
    __table_args__ = {'comment': 'Contains accessibility check results summary information.'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    status = Column(TINYINT(1), index=True)
    activities = Column(BIGINT(10))
    activitiespassed = Column(BIGINT(10))
    activitiesfailed = Column(BIGINT(10))
    errorschecktype1 = Column(BIGINT(10))
    errorschecktype2 = Column(BIGINT(10))
    errorschecktype3 = Column(BIGINT(10))
    errorschecktype4 = Column(BIGINT(10))
    errorschecktype5 = Column(BIGINT(10))
    errorschecktype6 = Column(BIGINT(10))
    errorschecktype7 = Column(BIGINT(10))
    failedchecktype1 = Column(BIGINT(10))
    failedchecktype2 = Column(BIGINT(10))
    failedchecktype3 = Column(BIGINT(10))
    failedchecktype4 = Column(BIGINT(10))
    failedchecktype5 = Column(BIGINT(10))
    failedchecktype6 = Column(BIGINT(10))
    failedchecktype7 = Column(BIGINT(10))
    percentchecktype1 = Column(BIGINT(10))
    percentchecktype2 = Column(BIGINT(10))
    percentchecktype3 = Column(BIGINT(10))
    percentchecktype4 = Column(BIGINT(10))
    percentchecktype5 = Column(BIGINT(10))
    percentchecktype6 = Column(BIGINT(10))
    percentchecktype7 = Column(BIGINT(10))


class MToolCohortrole(Base):
    __tablename__ = 'm_tool_cohortroles'
    __table_args__ = (
        Index('m_toolcoho_cohroluse_uix', 'cohortid', 'roleid', 'userid', unique=True),
        {'comment': 'Mapping of users to cohort role assignments.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    cohortid = Column(BIGINT(10), nullable=False)
    roleid = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    usermodified = Column(BIGINT(10))


class MToolCustomlang(Base):
    __tablename__ = 'm_tool_customlang'
    __table_args__ = (
        Index('m_toolcust_lancomstr_uix', 'lang', 'componentid', 'stringid', unique=True),
        {'comment': 'Contains the working checkout of all strings and their custo'}
    )

    id = Column(BIGINT(10), primary_key=True)
    lang = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    componentid = Column(BIGINT(10), nullable=False, index=True)
    stringid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    original = Column(LONGTEXT, nullable=False)
    master = Column(LONGTEXT)
    local = Column(LONGTEXT)
    timemodified = Column(BIGINT(10), nullable=False)
    timecustomized = Column(BIGINT(10))
    outdated = Column(SMALLINT(3), server_default=text("'0'"))
    modified = Column(SMALLINT(3), server_default=text("'0'"))


class MToolCustomlangComponent(Base):
    __tablename__ = 'm_tool_customlang_components'
    __table_args__ = {'comment': 'Contains the list of all installed plugins that provide thei'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    version = Column(String(255, 'utf8mb4_bin'))


class MToolDataprivacyCategory(Base):
    __tablename__ = 'm_tool_dataprivacy_category'
    __table_args__ = {'comment': 'Data categories'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(1))
    usermodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MToolDataprivacyCtxexpired(Base):
    __tablename__ = 'm_tool_dataprivacy_ctxexpired'
    __table_args__ = {'comment': 'Default comment for the table, please edit me'}

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, unique=True)
    unexpiredroles = Column(LONGTEXT)
    expiredroles = Column(LONGTEXT)
    defaultexpired = Column(TINYINT(1), nullable=False)
    status = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    usermodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MToolDataprivacyCtxinstance(Base):
    __tablename__ = 'm_tool_dataprivacy_ctxinstance'
    __table_args__ = {'comment': 'Default comment for the table, please edit me'}

    id = Column(BIGINT(10), primary_key=True)
    contextid = Column(BIGINT(10), nullable=False, unique=True)
    purposeid = Column(BIGINT(10), index=True)
    categoryid = Column(BIGINT(10), index=True)
    usermodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MToolDataprivacyCtxlevel(Base):
    __tablename__ = 'm_tool_dataprivacy_ctxlevel'
    __table_args__ = {'comment': 'Default comment for the table, please edit me'}

    id = Column(BIGINT(10), primary_key=True)
    contextlevel = Column(SMALLINT(3), nullable=False, unique=True)
    purposeid = Column(BIGINT(10), index=True)
    categoryid = Column(BIGINT(10), index=True)
    usermodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MToolDataprivacyPurpose(Base):
    __tablename__ = 'm_tool_dataprivacy_purpose'
    __table_args__ = {'comment': 'Data purposes'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(1))
    lawfulbases = Column(LONGTEXT, nullable=False)
    sensitivedatareasons = Column(LONGTEXT)
    retentionperiod = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    protected = Column(TINYINT(1))
    usermodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MToolDataprivacyPurposerole(Base):
    __tablename__ = 'm_tool_dataprivacy_purposerole'
    __table_args__ = (
        Index('m_tooldatapurp_purrol_uix', 'purposeid', 'roleid', unique=True),
        {'comment': 'Data purpose overrides for a specific role'}
    )

    id = Column(BIGINT(10), primary_key=True)
    purposeid = Column(BIGINT(10), nullable=False, index=True)
    roleid = Column(BIGINT(10), nullable=False, index=True)
    lawfulbases = Column(LONGTEXT)
    sensitivedatareasons = Column(LONGTEXT)
    retentionperiod = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    protected = Column(TINYINT(1))
    usermodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MToolDataprivacyRequest(Base):
    __tablename__ = 'm_tool_dataprivacy_request'
    __table_args__ = {'comment': 'Table for data requests'}

    id = Column(BIGINT(10), primary_key=True)
    type = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    comments = Column(LONGTEXT)
    commentsformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    requestedby = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    status = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    dpo = Column(BIGINT(10), index=True, server_default=text("'0'"))
    dpocomment = Column(LONGTEXT)
    dpocommentformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    systemapproved = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    usermodified = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    creationmethod = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MToolMonitorEvent(Base):
    __tablename__ = 'm_tool_monitor_events'
    __table_args__ = {'comment': 'A table that keeps a log of events related to subscriptions'}

    id = Column(BIGINT(10), primary_key=True)
    eventname = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    contextid = Column(BIGINT(10), nullable=False)
    contextlevel = Column(BIGINT(10), nullable=False)
    contextinstanceid = Column(BIGINT(10), nullable=False)
    link = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    courseid = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)


class MToolMonitorHistory(Base):
    __tablename__ = 'm_tool_monitor_history'
    __table_args__ = (
        Index('m_toolmonihist_sidusetim_uix', 'sid', 'userid', 'timesent', unique=True),
        {'comment': 'Table to store history of message notifications sent'}
    )

    id = Column(BIGINT(10), primary_key=True)
    sid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False)
    timesent = Column(BIGINT(10), nullable=False)


class MToolMonitorRule(Base):
    __tablename__ = 'm_tool_monitor_rules'
    __table_args__ = (
        Index('m_toolmonirule_couuse_ix', 'courseid', 'userid'),
        {'comment': 'Table to store rules'}
    )

    id = Column(BIGINT(10), primary_key=True)
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(1), nullable=False)
    name = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    userid = Column(BIGINT(10), nullable=False)
    courseid = Column(BIGINT(10), nullable=False)
    plugin = Column(String(254, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    eventname = Column(String(254, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    template = Column(LONGTEXT, nullable=False)
    templateformat = Column(TINYINT(1), nullable=False)
    frequency = Column(SMALLINT(4), nullable=False)
    timewindow = Column(MEDIUMINT(5), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)


class MToolMonitorSubscription(Base):
    __tablename__ = 'm_tool_monitor_subscriptions'
    __table_args__ = (
        Index('m_toolmonisubs_couuse_ix', 'courseid', 'userid'),
        {'comment': 'Table to store user subscriptions to various rules'}
    )

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False)
    ruleid = Column(BIGINT(10), nullable=False, index=True)
    cmid = Column(BIGINT(10), nullable=False)
    userid = Column(BIGINT(10), nullable=False)
    timecreated = Column(BIGINT(10), nullable=False)
    lastnotificationsent = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    inactivedate = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MToolPolicy(Base):
    __tablename__ = 'm_tool_policy'
    __table_args__ = {'comment': 'Contains the list of policy documents defined on the site.'}

    id = Column(BIGINT(10), primary_key=True)
    sortorder = Column(MEDIUMINT(5), nullable=False, server_default=text("'999'"))
    currentversionid = Column(BIGINT(10), index=True)


class MToolPolicyAcceptance(Base):
    __tablename__ = 'm_tool_policy_acceptances'
    __table_args__ = (
        Index('m_toolpoliacce_poluse_uix', 'policyversionid', 'userid', unique=True),
        {'comment': 'Tracks users accepting the policy versions'}
    )

    id = Column(BIGINT(10), primary_key=True)
    policyversionid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    status = Column(TINYINT(1))
    lang = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    usermodified = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    note = Column(LONGTEXT)


class MToolPolicyVersion(Base):
    __tablename__ = 'm_tool_policy_versions'
    __table_args__ = {'comment': 'Holds versions of the policy documents'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(1333, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    type = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    audience = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    archived = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    usermodified = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    policyid = Column(BIGINT(10), nullable=False, index=True)
    agreementstyle = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    optional = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    revision = Column(String(1333, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    summary = Column(LONGTEXT, nullable=False)
    summaryformat = Column(SMALLINT(3), nullable=False)
    content = Column(LONGTEXT, nullable=False)
    contentformat = Column(SMALLINT(3), nullable=False)


class MToolRecyclebinCategory(Base):
    __tablename__ = 'm_tool_recyclebin_category'
    __table_args__ = {'comment': 'A list of items in the category recycle bin'}

    id = Column(BIGINT(10), primary_key=True)
    categoryid = Column(BIGINT(10), nullable=False, index=True)
    shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    fullname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False, index=True)


class MToolRecyclebinCourse(Base):
    __tablename__ = 'm_tool_recyclebin_course'
    __table_args__ = {'comment': 'A list of items in the course recycle bin'}

    id = Column(BIGINT(10), primary_key=True)
    courseid = Column(BIGINT(10), nullable=False, index=True)
    section = Column(BIGINT(10), nullable=False)
    module = Column(BIGINT(10), nullable=False)
    name = Column(String(255, 'utf8mb4_bin'))
    timecreated = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))


class MToolUsertoursStep(Base):
    __tablename__ = 'm_tool_usertours_steps'
    __table_args__ = (
        Index('m_tooluserstep_tousor_ix', 'tourid', 'sortorder'),
        {'comment': 'Steps in an tour'}
    )

    id = Column(BIGINT(10), primary_key=True)
    tourid = Column(BIGINT(10), nullable=False, index=True)
    title = Column(LONGTEXT)
    content = Column(LONGTEXT)
    targettype = Column(TINYINT(2), nullable=False)
    targetvalue = Column(LONGTEXT, nullable=False)
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    configdata = Column(LONGTEXT, nullable=False)


class MToolUsertoursTour(Base):
    __tablename__ = 'm_tool_usertours_tours'
    __table_args__ = {'comment': 'List of tours'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    pathmatch = Column(String(255, 'utf8mb4_bin'))
    enabled = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    configdata = Column(LONGTEXT, nullable=False)


class MUpgradeLog(Base):
    __tablename__ = 'm_upgrade_log'
    __table_args__ = (
        Index('m_upgrlog_typtim_ix', 'type', 'timemodified'),
        {'comment': 'Upgrade logging'}
    )

    id = Column(BIGINT(10), primary_key=True)
    type = Column(BIGINT(10), nullable=False)
    plugin = Column(String(100, 'utf8mb4_bin'))
    version = Column(String(100, 'utf8mb4_bin'))
    targetversion = Column(String(100, 'utf8mb4_bin'))
    info = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    details = Column(LONGTEXT)
    backtrace = Column(LONGTEXT)
    userid = Column(BIGINT(10), nullable=False, index=True)
    timemodified = Column(BIGINT(10), nullable=False, index=True)


class MUrl(Base):
    __tablename__ = 'm_url'
    __table_args__ = {'comment': 'each record is one url resource'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    externalurl = Column(LONGTEXT, nullable=False)
    display = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    displayoptions = Column(LONGTEXT)
    parameters = Column(LONGTEXT)
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MUser(Base):
    __tablename__ = 'm_user'
    __table_args__ = (
        Index('m_user_mneuse_uix', 'mnethostid', 'username', unique=True),
        {'comment': 'One record for each person'}
    )

    id = Column(BIGINT(10), primary_key=True)
    auth = Column(String(20, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("'manual'"))
    confirmed = Column(TINYINT(1), nullable=False, index=True, server_default=text("'0'"))
    policyagreed = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    deleted = Column(TINYINT(1), nullable=False, index=True, server_default=text("'0'"))
    suspended = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    mnethostid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    username = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    password = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    idnumber = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    firstname = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    lastname = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    email = Column(String(100, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    emailstop = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    phone1 = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    phone2 = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    institution = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    department = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    address = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    city = Column(String(120, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    country = Column(String(2, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    lang = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("'en'"))
    calendartype = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("'gregorian'"))
    theme = Column(String(50, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timezone = Column(String(100, 'utf8mb4_bin'), nullable=False, server_default=text("'99'"))
    firstaccess = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastaccess = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    lastlogin = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    currentlogin = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lastip = Column(String(45, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    secret = Column(String(15, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    picture = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'1'"))
    mailformat = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    maildigest = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    maildisplay = Column(TINYINT(2), nullable=False, server_default=text("'2'"))
    autosubscribe = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    trackforums = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    trustbitmask = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    imagealt = Column(String(255, 'utf8mb4_bin'))
    lastnamephonetic = Column(String(255, 'utf8mb4_bin'), index=True)
    firstnamephonetic = Column(String(255, 'utf8mb4_bin'), index=True)
    middlename = Column(String(255, 'utf8mb4_bin'), index=True)
    alternatename = Column(String(255, 'utf8mb4_bin'), index=True)
    moodlenetprofile = Column(String(255, 'utf8mb4_bin'))


class MUserDevice(Base):
    __tablename__ = 'm_user_devices'
    __table_args__ = (
        Index('m_userdevi_uuiuse_ix', 'uuid', 'userid'),
        Index('m_userdevi_pususe_uix', 'pushid', 'userid', unique=True),
        {'comment': "This table stores user's mobile devices information in order"}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    appid = Column(String(128, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    name = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    model = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    platform = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    version = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    pushid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    uuid = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)


class MUserEnrolment(Base):
    __tablename__ = 'm_user_enrolments'
    __table_args__ = (
        Index('m_userenro_enruse_uix', 'enrolid', 'userid', unique=True),
        {'comment': 'Users participating in courses (aka enrolled users) - everyb'}
    )

    id = Column(BIGINT(10), primary_key=True)
    status = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    enrolid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    timestart = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timeend = Column(BIGINT(10), nullable=False, server_default=text("'2147483647'"))
    modifierid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MUserInfoCategory(Base):
    __tablename__ = 'm_user_info_category'
    __table_args__ = {'comment': 'Customisable fields categories'}

    id = Column(BIGINT(10), primary_key=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MUserInfoDatum(Base):
    __tablename__ = 'm_user_info_data'
    __table_args__ = (
        Index('m_userinfodata_usefie_uix', 'userid', 'fieldid', unique=True),
        {'comment': 'Data for the customisable user fields'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    fieldid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    data = Column(LONGTEXT, nullable=False)
    dataformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MUserInfoField(Base):
    __tablename__ = 'm_user_info_field'
    __table_args__ = {'comment': 'Customisable user profile fields'}

    id = Column(BIGINT(10), primary_key=True)
    shortname = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'shortname'"))
    name = Column(LONGTEXT, nullable=False)
    datatype = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    description = Column(LONGTEXT)
    descriptionformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    categoryid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    sortorder = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    required = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    locked = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    visible = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    forceunique = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    signup = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    defaultdata = Column(LONGTEXT)
    defaultdataformat = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    param1 = Column(LONGTEXT)
    param2 = Column(LONGTEXT)
    param3 = Column(LONGTEXT)
    param4 = Column(LONGTEXT)
    param5 = Column(LONGTEXT)


class MUserLastacces(Base):
    __tablename__ = 'm_user_lastaccess'
    __table_args__ = (
        Index('m_userlast_usecou_uix', 'userid', 'courseid', unique=True),
        {'comment': 'To keep track of course page access times, used in online pa'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    courseid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    timeaccess = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MUserPasswordHistory(Base):
    __tablename__ = 'm_user_password_history'
    __table_args__ = {'comment': 'A rotating log of hashes of previously used passwords for ea'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    hash = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    timecreated = Column(BIGINT(10), nullable=False)


class MUserPasswordReset(Base):
    __tablename__ = 'm_user_password_resets'
    __table_args__ = {'comment': 'table tracking password reset confirmation tokens'}

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    timerequested = Column(BIGINT(10), nullable=False)
    timererequested = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    token = Column(String(32, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MUserPreference(Base):
    __tablename__ = 'm_user_preferences'
    __table_args__ = (
        Index('m_userpref_usenam_uix', 'userid', 'name', unique=True),
        {'comment': 'Allows modules to store arbitrary user preferences'}
    )

    id = Column(BIGINT(10), primary_key=True)
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, index=True, server_default=text("''"))
    value = Column(String(1333, 'utf8mb4_bin'), nullable=False, server_default=text("''"))


class MUserPrivateKey(Base):
    __tablename__ = 'm_user_private_key'
    __table_args__ = (
        Index('m_userprivkey_scrval_ix', 'script', 'value'),
        {'comment': 'access keys used in cookieless scripts - rss, etc.'}
    )

    id = Column(BIGINT(10), primary_key=True)
    script = Column(String(128, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    value = Column(String(128, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    userid = Column(BIGINT(10), nullable=False, index=True)
    instance = Column(BIGINT(10))
    iprestriction = Column(String(255, 'utf8mb4_bin'))
    validuntil = Column(BIGINT(10))
    timecreated = Column(BIGINT(10))


class MWiki(Base):
    __tablename__ = 'm_wiki'
    __table_args__ = {'comment': 'Stores Wiki activity configuration'}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'Wiki'"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    firstpagetitle = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'First Page'"))
    wikimode = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'collaborative'"))
    defaultformat = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'creole'"))
    forceformat = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    editbegin = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    editend = Column(BIGINT(10), server_default=text("'0'"))


class MWikiLink(Base):
    __tablename__ = 'm_wiki_links'
    __table_args__ = {'comment': 'Page wiki links'}

    id = Column(BIGINT(10), primary_key=True)
    subwikiid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    frompageid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    topageid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    tomissingpage = Column(String(255, 'utf8mb4_bin'))


class MWikiLock(Base):
    __tablename__ = 'm_wiki_locks'
    __table_args__ = {'comment': 'Manages page locks'}

    id = Column(BIGINT(10), primary_key=True)
    pageid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    sectionname = Column(String(255, 'utf8mb4_bin'))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    lockedat = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MWikiPage(Base):
    __tablename__ = 'm_wiki_pages'
    __table_args__ = (
        Index('m_wikipage_subtituse_uix', 'subwikiid', 'title', 'userid', unique=True),
        {'comment': 'Stores wiki pages'}
    )

    id = Column(BIGINT(10), primary_key=True)
    subwikiid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    title = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'title'"))
    cachedcontent = Column(LONGTEXT, nullable=False)
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    timerendered = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    pageviews = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    readonly = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class MWikiSubwiki(Base):
    __tablename__ = 'm_wiki_subwikis'
    __table_args__ = (
        Index('m_wikisubw_wikgrouse_uix', 'wikiid', 'groupid', 'userid', unique=True),
        {'comment': 'Stores subwiki instances'}
    )

    id = Column(BIGINT(10), primary_key=True)
    wikiid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    groupid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MWikiSynonym(Base):
    __tablename__ = 'm_wiki_synonyms'
    __table_args__ = (
        Index('m_wikisyno_pagpag_uix', 'pageid', 'pagesynonym', unique=True),
        {'comment': 'Stores wiki pages synonyms'}
    )

    id = Column(BIGINT(10), primary_key=True)
    subwikiid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    pageid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    pagesynonym = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("'Pagesynonym'"))


class MWikiVersion(Base):
    __tablename__ = 'm_wiki_versions'
    __table_args__ = {'comment': 'Stores wiki page history'}

    id = Column(BIGINT(10), primary_key=True)
    pageid = Column(BIGINT(10), nullable=False, index=True, server_default=text("'0'"))
    content = Column(LONGTEXT, nullable=False)
    contentformat = Column(String(20, 'utf8mb4_bin'), nullable=False, server_default=text("'creole'"))
    version = Column(MEDIUMINT(5), nullable=False, server_default=text("'0'"))
    timecreated = Column(BIGINT(10), nullable=False, server_default=text("'0'"))
    userid = Column(BIGINT(10), nullable=False, server_default=text("'0'"))


class MWorkshop(Base):
    __tablename__ = 'm_workshop'
    __table_args__ = {'comment': 'This table keeps information about the module instances and '}

    id = Column(BIGINT(10), primary_key=True)
    course = Column(BIGINT(10), nullable=False, index=True)
    name = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    intro = Column(LONGTEXT)
    introformat = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    instructauthors = Column(LONGTEXT)
    instructauthorsformat = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    instructreviewers = Column(LONGTEXT)
    instructreviewersformat = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    timemodified = Column(BIGINT(10), nullable=False)
    phase = Column(SMALLINT(3), server_default=text("'0'"))
    useexamples = Column(TINYINT(2), server_default=text("'0'"))
    usepeerassessment = Column(TINYINT(2), server_default=text("'0'"))
    useselfassessment = Column(TINYINT(2), server_default=text("'0'"))
    grade = Column(DECIMAL(10, 5), server_default=text("'80.00000'"))
    gradinggrade = Column(DECIMAL(10, 5), server_default=text("'20.00000'"))
    strategy = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    evaluation = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    gradedecimals = Column(SMALLINT(3), server_default=text("'0'"))
    submissiontypetext = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    submissiontypefile = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    nattachments = Column(SMALLINT(3), server_default=text("'1'"))
    submissionfiletypes = Column(String(255, 'utf8mb4_bin'))
    latesubmissions = Column(TINYINT(2), server_default=text("'0'"))
    maxbytes = Column(BIGINT(10), server_default=text("'100000'"))
    examplesmode = Column(SMALLINT(3), server_default=text("'0'"))
    submissionstart = Column(BIGINT(10), server_default=text("'0'"))
    submissionend = Column(BIGINT(10), server_default=text("'0'"))
    assessmentstart = Column(BIGINT(10), server_default=text("'0'"))
    assessmentend = Column(BIGINT(10), server_default=text("'0'"))
    phaseswitchassessment = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    conclusion = Column(LONGTEXT)
    conclusionformat = Column(SMALLINT(3), nullable=False, server_default=text("'1'"))
    overallfeedbackmode = Column(SMALLINT(3), server_default=text("'1'"))
    overallfeedbackfiles = Column(SMALLINT(3), server_default=text("'0'"))
    overallfeedbackfiletypes = Column(String(255, 'utf8mb4_bin'))
    overallfeedbackmaxbytes = Column(BIGINT(10), server_default=text("'100000'"))


class MWorkshopAggregation(Base):
    __tablename__ = 'm_workshop_aggregations'
    __table_args__ = (
        Index('m_workaggr_woruse_uix', 'workshopid', 'userid', unique=True),
        {'comment': 'Aggregated grades for assessment are stored here. The aggreg'}
    )

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, index=True)
    userid = Column(BIGINT(10), nullable=False, index=True)
    gradinggrade = Column(DECIMAL(10, 5))
    timegraded = Column(BIGINT(10))


class MWorkshopAssessment(Base):
    __tablename__ = 'm_workshop_assessments'
    __table_args__ = {'comment': 'Info about the made assessment and automatically calculated '}

    id = Column(BIGINT(10), primary_key=True)
    submissionid = Column(BIGINT(10), nullable=False, index=True)
    reviewerid = Column(BIGINT(10), nullable=False, index=True)
    weight = Column(BIGINT(10), nullable=False, server_default=text("'1'"))
    timecreated = Column(BIGINT(10), server_default=text("'0'"))
    timemodified = Column(BIGINT(10), server_default=text("'0'"))
    grade = Column(DECIMAL(10, 5))
    gradinggrade = Column(DECIMAL(10, 5))
    gradinggradeover = Column(DECIMAL(10, 5))
    gradinggradeoverby = Column(BIGINT(10), index=True)
    feedbackauthor = Column(LONGTEXT)
    feedbackauthorformat = Column(SMALLINT(3), server_default=text("'0'"))
    feedbackauthorattachment = Column(SMALLINT(3), server_default=text("'0'"))
    feedbackreviewer = Column(LONGTEXT)
    feedbackreviewerformat = Column(SMALLINT(3), server_default=text("'0'"))


class MWorkshopGrade(Base):
    __tablename__ = 'm_workshop_grades'
    __table_args__ = (
        Index('m_workgrad_assstrdim_uix', 'assessmentid', 'strategy', 'dimensionid', unique=True),
        {'comment': 'How the reviewers filled-up the grading forms, given grades '}
    )

    id = Column(BIGINT(10), primary_key=True)
    assessmentid = Column(BIGINT(10), nullable=False, index=True)
    strategy = Column(String(30, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    dimensionid = Column(BIGINT(10), nullable=False)
    grade = Column(DECIMAL(10, 5))
    peercomment = Column(LONGTEXT)
    peercommentformat = Column(SMALLINT(3), server_default=text("'0'"))


class MWorkshopSubmission(Base):
    __tablename__ = 'm_workshop_submissions'
    __table_args__ = {'comment': 'Info about the submission and the aggregation of the grade f'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, index=True)
    example = Column(TINYINT(2), server_default=text("'0'"))
    authorid = Column(BIGINT(10), nullable=False, index=True)
    timecreated = Column(BIGINT(10), nullable=False)
    timemodified = Column(BIGINT(10), nullable=False)
    title = Column(String(255, 'utf8mb4_bin'), nullable=False, server_default=text("''"))
    content = Column(LONGTEXT)
    contentformat = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    contenttrust = Column(SMALLINT(3), nullable=False, server_default=text("'0'"))
    attachment = Column(TINYINT(2), server_default=text("'0'"))
    grade = Column(DECIMAL(10, 5))
    gradeover = Column(DECIMAL(10, 5))
    gradeoverby = Column(BIGINT(10), index=True)
    feedbackauthor = Column(LONGTEXT)
    feedbackauthorformat = Column(SMALLINT(3), server_default=text("'0'"))
    timegraded = Column(BIGINT(10))
    published = Column(TINYINT(2), server_default=text("'0'"))
    late = Column(TINYINT(2), nullable=False, server_default=text("'0'"))


class MWorkshopallocationScheduled(Base):
    __tablename__ = 'm_workshopallocation_scheduled'
    __table_args__ = {'comment': 'Stores the allocation settings for the scheduled allocator'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, unique=True)
    enabled = Column(TINYINT(2), nullable=False, server_default=text("'0'"))
    submissionend = Column(BIGINT(10), nullable=False)
    timeallocated = Column(BIGINT(10))
    settings = Column(LONGTEXT)
    resultstatus = Column(BIGINT(10))
    resultmessage = Column(String(1333, 'utf8mb4_bin'))
    resultlog = Column(LONGTEXT)


class MWorkshopevalBestSetting(Base):
    __tablename__ = 'm_workshopeval_best_settings'
    __table_args__ = {'comment': 'Settings for the grading evaluation subplugin Comparison wit'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, unique=True)
    comparison = Column(SMALLINT(3), server_default=text("'5'"))


class MWorkshopformAccumulative(Base):
    __tablename__ = 'm_workshopform_accumulative'
    __table_args__ = {'comment': 'The assessment dimensions definitions of Accumulative gradin'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, index=True)
    sort = Column(BIGINT(10), server_default=text("'0'"))
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(3), server_default=text("'0'"))
    grade = Column(BIGINT(10), nullable=False)
    weight = Column(MEDIUMINT(5), server_default=text("'1'"))


class MWorkshopformComment(Base):
    __tablename__ = 'm_workshopform_comments'
    __table_args__ = {'comment': 'The assessment dimensions definitions of Comments strategy f'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, index=True)
    sort = Column(BIGINT(10), server_default=text("'0'"))
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(3), server_default=text("'0'"))


class MWorkshopformNumerror(Base):
    __tablename__ = 'm_workshopform_numerrors'
    __table_args__ = {'comment': 'The assessment dimensions definitions of Number of errors gr'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, index=True)
    sort = Column(BIGINT(10), server_default=text("'0'"))
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(3), server_default=text("'0'"))
    descriptiontrust = Column(BIGINT(10))
    grade0 = Column(String(50, 'utf8mb4_bin'))
    grade1 = Column(String(50, 'utf8mb4_bin'))
    weight = Column(MEDIUMINT(5), server_default=text("'1'"))


class MWorkshopformNumerrorsMap(Base):
    __tablename__ = 'm_workshopform_numerrors_map'
    __table_args__ = (
        Index('m_worknumemap_wornon_uix', 'workshopid', 'nonegative', unique=True),
        {'comment': 'This maps the number of errors to a percentual grade for sub'}
    )

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, index=True)
    nonegative = Column(BIGINT(10), nullable=False)
    grade = Column(DECIMAL(10, 5), nullable=False)


class MWorkshopformRubric(Base):
    __tablename__ = 'm_workshopform_rubric'
    __table_args__ = {'comment': 'The assessment dimensions definitions of Rubric grading stra'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, index=True)
    sort = Column(BIGINT(10), server_default=text("'0'"))
    description = Column(LONGTEXT)
    descriptionformat = Column(SMALLINT(3), server_default=text("'0'"))


class MWorkshopformRubricConfig(Base):
    __tablename__ = 'm_workshopform_rubric_config'
    __table_args__ = {'comment': 'Configuration table for the Rubric grading strategy'}

    id = Column(BIGINT(10), primary_key=True)
    workshopid = Column(BIGINT(10), nullable=False, unique=True)
    layout = Column(String(30, 'utf8mb4_bin'), server_default=text("'list'"))


class MWorkshopformRubricLevel(Base):
    __tablename__ = 'm_workshopform_rubric_levels'
    __table_args__ = {'comment': 'The definition of rubric rating scales'}

    id = Column(BIGINT(10), primary_key=True)
    dimensionid = Column(BIGINT(10), nullable=False, index=True)
    grade = Column(DECIMAL(10, 5), nullable=False)
    definition = Column(LONGTEXT)
    definitionformat = Column(SMALLINT(3), server_default=text("'0'"))




def connect_to_moodle_db(host='127.0.0.1', port=3306, user='moodle', pwd='m@0dl3ing', dbname='moodle'):
	print("connecting...")
	print(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4")
	engine = create_engine(f"mysql+pymysql://{user}:{urlquote(pwd)}@{host}:{port}/{dbname}?charset=utf8mb4", echo=False, future=True)
	conn = engine.connect()
	print("done")
	return engine, conn

engine, conn = connect_to_moodle_db()
Session = sessionmaker()
Session.configure(bind=engine)
Base.metadata.create_all(engine)

with Session() as session:
    for lesson in session.query(MLesson).all():
        lesson: MLesson = lesson
        print("Lesson", lesson)
        for page in session.query(MLessonPage).filter_by(lessonid=lesson.id).all():
            page: MLessonPage = page
            print(" found page", page.contents)

conn.close()