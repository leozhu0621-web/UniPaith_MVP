from unipaith.models.admin_audit_event import AdminAuditEvent
from unipaith.models.knowledge import (
    AdvisorPersona,
    CrawlFrontier,
    EngineDirective,
    InteractionSignal,
    KnowledgeDocument,
    KnowledgeLink,
    PersonInsight,
)
from unipaith.models.application import (
    Application,
    ApplicationChecklist,
    ApplicationScore,
    ApplicationSubmission,
    EnrollmentRecord,
    HistoricalOutcome,
    Interview,
    InterviewScore,
    OfferLetter,
    ReviewAssignment,
    Rubric,
)
from unipaith.models.base import Base
from unipaith.models.crawler import (
    CrawlJob,
    CrawlSchedule,
    EnrichmentRecord,
    ExtractedProgram,
    SourceURLPattern,
)
from unipaith.models.engagement import (
    Conversation,
    CRMRecord,
    Message,
    SavedList,
    SavedListItem,
    StudentCalendar,
    StudentEngagementSignal,
    StudentEssay,
    StudentResume,
)
from unipaith.models.institution import (
    Campaign,
    CampaignRecipient,
    Event,
    EventRSVP,
    Institution,
    Program,
    Reviewer,
    TargetSegment,
)
from unipaith.models.matching import (
    DataSource,
    Embedding,
    InstitutionFeature,
    MatchResult,
    ModelRegistry,
    OfferComparison,
    PredictionLog,
    RawIngestedData,
    StudentFeature,
)
from unipaith.models.ml_loop import (
    ABTestAssignment,
    DriftSnapshot,
    EvaluationRun,
    FairnessReport,
    OutcomeRecord,
    TrainingRun,
)
from unipaith.models.student import (
    AcademicRecord,
    Activity,
    OnboardingProgress,
    RecommendationRequest,
    StudentDocument,
    StudentPreference,
    StudentProfile,
    TestScore,
)
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import (
    Notification,
    NotificationPreference,
    Touchpoint,
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
    "AdminAuditEvent",
    "KnowledgeDocument", "KnowledgeLink", "CrawlFrontier",
    "EngineDirective", "InteractionSignal", "PersonInsight",
    "AdvisorPersona",
]
