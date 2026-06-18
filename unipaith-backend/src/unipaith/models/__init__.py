from unipaith.models.admin_audit_event import AdminAuditEvent
from unipaith.models.ai_artifacts import (
    AiTurn,
    MatchRationale,
    StudentFeatureVector,
)
from unipaith.models.ai_feedback import AiTurnFeedback
from unipaith.models.application import (
    AIPacketSummary,
    Application,
    ApplicationChecklist,
    ApplicationScore,
    ApplicationSubmission,
    EnrollmentRecord,
    HistoricalOutcome,
    IntegritySignal,
    Interview,
    InterviewScore,
    OfferLetter,
    ReviewAssignment,
    Rubric,
)
from unipaith.models.attribution import AttributionEvent
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.base import Base
from unipaith.models.billing import StudentSubscription
from unipaith.models.confidence_outcome import ConfidenceOutcomePair
from unipaith.models.crawler import (
    ChangeEvent,
    CrawlSource,
    EntityEnrichment,
    KnowledgeEntity,
)
from unipaith.models.discovery import DiscoveryMessage, DiscoverySession
from unipaith.models.engagement import (
    CalendarItemState,
    Conversation,
    ConversationSession,
    CRMRecord,
    Message,
    SavedList,
    SavedListItem,
    StudentCalendar,
    StudentCompareItem,
    StudentEngagementSignal,
    StudentEssay,
    StudentResume,
)
from unipaith.models.eval_harness import EvalCase, EvalResult
from unipaith.models.fairness import FairnessOverride, FairnessSignal
from unipaith.models.feedback import Feedback
from unipaith.models.follow import InstitutionFollow
from unipaith.models.goals import StudentGoal
from unipaith.models.graduate import (
    AdvisorMatch,
    Department,
    DepartmentReview,
    FacultyProfile,
    FundingPackage,
    FundingPackageComponent,
    FundingPool,
    GraduateIntent,
)
from unipaith.models.identity import StudentIdentity
from unipaith.models.institution import (
    Campaign,
    CampaignAction,
    CampaignLink,
    CampaignRecipient,
    CampaignSuppression,
    CommunicationTemplate,
    DatasetMappingTemplate,
    DatasetVersion,
    EmployerFeedback,
    Event,
    EventRSVP,
    Inquiry,
    Institution,
    InstitutionDataset,
    InstitutionPost,
    IntakeRound,
    Program,
    ProgramChecklistItem,
    ProgramPreference,
    Promotion,
    Reviewer,
    School,
    StudentProgramReview,
    TargetSegment,
    UploadedContact,
    UploadedList,
)
from unipaith.models.intake import (
    RawInput,
    SignalChangeEvent,
    SignalClarification,
    StudentSignal,
)
from unipaith.models.international import (
    CountryRequirementPack,
    InternationalProcessing,
)
from unipaith.models.knowledge import (
    AdvisorPersona,
    CrawlFrontier,
    EngineDirective,
    EngineLoopSnapshot,
    InteractionSignal,
    KnowledgeDocument,
    KnowledgeLink,
    PersonInsight,
)
from unipaith.models.major_specific import StudentMajorSpecificSignals
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
from unipaith.models.material_ingest import MaterialIngest
from unipaith.models.ml_loop import (
    ABTestAssignment,
    DriftSnapshot,
    EvaluationRun,
    FairnessReport,
    OutcomeRecord,
    TrainingRun,
)
from unipaith.models.needs import StudentNeed
from unipaith.models.outcomes import (
    ProgramAdmissionsHistory,
    ProgramOutcome,
    ProgramTopEmployer,
    ReviewThemeSummary,
    SchoolAdmissionsHistory,
    SchoolOutcome,
)
from unipaith.models.payment import Payment
from unipaith.models.peer import PeerConnection, PeerProfile, PeerReport
from unipaith.models.pipeline import (
    PipelineConfig,
    PipelineStageSnapshot,
)
from unipaith.models.prompt_library import (
    BehavioralPrompt,
    StudentBehavioralResponse,
    StudentStory,
)
from unipaith.models.recruitment import (
    Prospect,
    RecruitmentFair,
    RecruitmentTrip,
    Territory,
    TripVisit,
)
from unipaith.models.reference import (
    RefAccreditation,
    ReferenceEntity,
    RefGeoCost,
    RefMajor,
    RefOccupation,
    RefRanking,
    RefTest,
    RefVisa,
    Scholarship,
)
from unipaith.models.saved_search import SavedSearch
from unipaith.models.scholarship import Scholarship as ExternalScholarship
from unipaith.models.settings import InstitutionTeamInvite, UserSettings
from unipaith.models.strategy import StudentStrategy
from unipaith.models.student import (
    AcademicRecord,
    Activity,
    OnboardingProgress,
    RecommendationRequest,
    StudentAccommodation,
    StudentCompetition,
    StudentCourse,
    StudentDataConsent,
    StudentDocument,
    StudentLanguage,
    StudentOnlinePresence,
    StudentPortfolioItem,
    StudentPreference,
    StudentProfile,
    StudentResearch,
    StudentScheduling,
    StudentVisaInfo,
    StudentWorkExperience,
    TestScore,
)
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import (
    Notification,
    NotificationPreference,
    Touchpoint,
)
from unipaith.models.workshops import WorkshopFeedbackRun

__all__ = [
    "Base",
    "User",
    "UserRole",
    "StudentProfile",
    "AcademicRecord",
    "TestScore",
    "Activity",
    "StudentDocument",
    "StudentPreference",
    "RecommendationRequest",
    "StudentAccommodation",
    "StudentCompetition",
    "StudentCourse",
    "StudentDataConsent",
    "StudentLanguage",
    "StudentOnlinePresence",
    "StudentPortfolioItem",
    "StudentResearch",
    "StudentScheduling",
    "StudentVisaInfo",
    "StudentWorkExperience",
    "OnboardingProgress",
    # Discovery (Phase A — parallel session, merged in #111)
    "DiscoverySession",
    "DiscoveryMessage",
    # Adaptive Intake Engine (Spec 44 — four-layer signal pipeline)
    "RawInput",
    "StudentSignal",
    "SignalChangeEvent",
    "SignalClarification",
    # Discovery artifacts (Phase A — parallel session, merged in #113)
    "StudentGoal",
    "StudentNeed",
    "StudentIdentity",
    "MaterialIngest",
    "StudentStrategy",
    "WorkshopFeedbackRun",
    "BehavioralPrompt",
    "StudentBehavioralResponse",
    "StudentStory",
    # Spec 43 — major-specific field catalog
    "StudentMajorSpecificSignals",
    # LLM-only artifacts (Phase A1)
    "StudentFeatureVector",
    "AiTurn",
    "MatchRationale",
    "AiTurnFeedback",
    "ConfidenceOutcomePair",
    "Institution",
    "School",
    "Program",
    "ProgramPreference",
    "TargetSegment",
    "Campaign",
    "CampaignLink",
    "CampaignAction",
    "CampaignRecipient",
    "CampaignSuppression",
    "UploadedList",
    "UploadedContact",
    "CommunicationTemplate",
    "Event",
    "EventRSVP",
    "Inquiry",
    "Reviewer",
    "InstitutionDataset",
    "DatasetVersion",
    "DatasetMappingTemplate",
    "IntakeRound",
    "ProgramChecklistItem",
    "InstitutionPost",
    "Promotion",
    "StudentProgramReview",
    "EmployerFeedback",
    "HistoricalOutcome",
    "AIPacketSummary",
    "IntegritySignal",
    "Application",
    "ApplicationChecklist",
    "ApplicationSubmission",
    "ReviewAssignment",
    "Rubric",
    "ApplicationScore",
    "Interview",
    "InterviewScore",
    "OfferLetter",
    "EnrollmentRecord",
    "StudentEngagementSignal",
    "AttributionEvent",
    "InstitutionFollow",
    "PeerProfile",
    "PeerConnection",
    "PeerReport",
    "SavedList",
    "SavedListItem",
    "StudentCompareItem",
    "StudentCalendar",
    "CalendarItemState",
    "CRMRecord",
    "Conversation",
    "ConversationSession",
    "Message",
    "StudentResume",
    "StudentEssay",
    "MatchResult",
    "StudentFeature",
    "InstitutionFeature",
    "Embedding",
    "PredictionLog",
    "ModelRegistry",
    "DataSource",
    "RawIngestedData",
    "OfferComparison",
    "Notification",
    "NotificationPreference",
    "Touchpoint",
    # Settings (Spec 21)
    "UserSettings",
    "InstitutionTeamInvite",
    "OutcomeRecord",
    "EvaluationRun",
    "TrainingRun",
    "ABTestAssignment",
    "DriftSnapshot",
    "FairnessReport",
    # Eval harness (Spec 62 §8 — shared golden-set + results)
    "EvalCase",
    "EvalResult",
    "AdminAuditEvent",
    "AdmissionsAuditLog",
    # Fairness governance (Spec 46 §6 — disparate-impact auto-halt)
    "FairnessSignal",
    "FairnessOverride",
    # International admissions (Spec 38)
    "InternationalProcessing",
    "CountryRequirementPack",
    "KnowledgeDocument",
    "KnowledgeLink",
    "CrawlFrontier",
    # Spec 60 — knowledge engine + reference projection
    "CrawlSource",
    "KnowledgeEntity",
    "EntityEnrichment",
    "ChangeEvent",
    "Scholarship",
    # External scholarships catalog (Spec 2026-06-14 — CareerOneStop)
    "ExternalScholarship",
    "RefOccupation",
    "RefTest",
    "RefVisa",
    "RefGeoCost",
    "RefMajor",
    "RefRanking",
    "RefAccreditation",
    "ReferenceEntity",
    "EngineLoopSnapshot",
    "EngineDirective",
    "InteractionSignal",
    "PersonInsight",
    "AdvisorPersona",
    "PipelineStageSnapshot",
    "PipelineConfig",
    "StudentSubscription",
    # Payments (Spec 39)
    "Payment",
    # Saved searches + alerts (Spec 56)
    "SavedSearch",
    # Recruitment CRM (Spec 40)
    "Prospect",
    "RecruitmentTrip",
    "TripVisit",
    "RecruitmentFair",
    "Territory",
    # Graduate & PhD admissions (Spec 41)
    "Department",
    "FacultyProfile",
    "GraduateIntent",
    "AdvisorMatch",
    "FundingPool",
    "FundingPackage",
    "FundingPackageComponent",
    "DepartmentReview",
    # Outcomes & admissions-history data layer (Spec 68)
    "ProgramOutcome",
    "ProgramTopEmployer",
    "ProgramAdmissionsHistory",
    "SchoolOutcome",
    "SchoolAdmissionsHistory",
    "ReviewThemeSummary",
    # Demo feedback survey
    "Feedback",
]
