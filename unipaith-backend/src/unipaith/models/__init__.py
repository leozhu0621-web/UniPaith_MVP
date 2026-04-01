from unipaith.models.base import Base
from unipaith.models.user import User, UserRole
from unipaith.models.student import (
    StudentProfile, AcademicRecord, TestScore, Activity,
    StudentDocument, StudentPreference, RecommendationRequest,
    OnboardingProgress,
)
from unipaith.models.institution import (
    Institution, Program, TargetSegment, Campaign, CampaignRecipient,
    Event, EventRSVP, Reviewer,
)
from unipaith.models.application import (
    HistoricalOutcome, Application, ApplicationChecklist,
    ApplicationSubmission, ReviewAssignment, Rubric,
    ApplicationScore, Interview, InterviewScore,
    OfferLetter, EnrollmentRecord,
)
from unipaith.models.engagement import (
    StudentEngagementSignal, SavedList, SavedListItem,
    StudentCalendar, CRMRecord, Conversation, Message,
    StudentResume, StudentEssay,
)
from unipaith.models.matching import (
    MatchResult, StudentFeature, InstitutionFeature,
    Embedding, PredictionLog, ModelRegistry,
    DataSource, RawIngestedData, OfferComparison,
)
from unipaith.models.workflow import (
    Notification, NotificationPreference, Touchpoint,
)
from unipaith.models.ml_loop import (
    OutcomeRecord, EvaluationRun, TrainingRun,
    ABTestAssignment, DriftSnapshot, FairnessReport,
)
from unipaith.models.crawler import (
    CrawlJob, ExtractedProgram, CrawlSchedule,
    SourceURLPattern, EnrichmentRecord,
)

__all__ = [
    "Base", "User", "UserRole",
    "StudentProfile", "AcademicRecord", "TestScore", "Activity",
    "StudentDocument", "StudentPreference", "RecommendationRequest",
    "OnboardingProgress",
    "Institution", "Program", "TargetSegment", "Campaign", "CampaignRecipient",
    "Event", "EventRSVP", "Reviewer",
    "HistoricalOutcome", "Application", "ApplicationChecklist",
    "ApplicationSubmission", "ReviewAssignment", "Rubric",
    "ApplicationScore", "Interview", "InterviewScore",
    "OfferLetter", "EnrollmentRecord",
    "StudentEngagementSignal", "SavedList", "SavedListItem",
    "StudentCalendar", "CRMRecord", "Conversation", "Message",
    "StudentResume", "StudentEssay",
    "MatchResult", "StudentFeature", "InstitutionFeature",
    "Embedding", "PredictionLog", "ModelRegistry",
    "DataSource", "RawIngestedData", "OfferComparison",
    "Notification", "NotificationPreference", "Touchpoint",
    "OutcomeRecord", "EvaluationRun", "TrainingRun",
    "ABTestAssignment", "DriftSnapshot", "FairnessReport",
    "CrawlJob", "ExtractedProgram", "CrawlSchedule",
    "SourceURLPattern", "EnrichmentRecord",
]
