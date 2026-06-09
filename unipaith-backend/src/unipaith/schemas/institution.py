from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Institution ---


class CreateInstitutionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: Literal["university", "college", "technical_institute", "community_college"]
    country: str = Field(min_length=1, max_length=100)
    region: str | None = None
    city: str | None = None
    description_text: str | None = None
    campus_description: str | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    student_body_size: int | None = None
    founded_year: int | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    media_gallery: list[str] | None = None
    social_links: dict | None = None


class ClaimInstitutionRequest(BaseModel):
    extracted_ids: list[UUID] = Field(min_length=1)


class UnclaimedInstitutionResult(BaseModel):
    institution_name: str
    institution_country: str | None = None
    institution_city: str | None = None
    institution_type: str | None = None
    institution_website: str | None = None
    program_count: int
    extracted_ids: list[UUID]


class UpdateInstitutionRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: Literal["university", "college", "technical_institute", "community_college"] | None = None
    country: str | None = Field(None, min_length=1, max_length=100)
    region: str | None = None
    city: str | None = None
    description_text: str | None = None
    campus_description: str | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    student_body_size: int | None = None
    founded_year: int | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    media_gallery: list[str] | None = None
    social_links: dict | None = None
    inquiry_routing: dict | None = None
    # Institution-profile JSONB dicts surfaced on the student view and the
    # admin SettingsPage. Previously missing from UpdateInstitutionRequest,
    # which made these fields read-only via the API.
    support_services: dict | None = None
    policies: dict | None = None
    international_info: dict | None = None
    school_outcomes: dict | None = None
    # Spec 25 §7 — campaign approval workflow toggle.
    require_campaign_approval: bool | None = None
    # Spec 22 §3 Identity — editable accreditation (stored in ranking_data.accreditor).
    accreditation: str | None = None


class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    type: str
    country: str
    region: str | None
    city: str | None
    ranking_data: dict | None = None
    description_text: str | None
    campus_description: str | None = None
    campus_setting: str | None = None
    student_body_size: int | None = None
    founded_year: int | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    logo_url: str | None
    website_url: str | None
    media_gallery: list | dict | None = None
    social_links: dict | None = None
    inquiry_routing: dict | None = None
    support_services: dict | None = None
    policies: dict | None = None
    international_info: dict | None = None
    school_outcomes: dict | None = None
    is_verified: bool
    require_campaign_approval: bool = False
    setup_complete: bool = False
    setup_state: dict | None = None
    created_at: datetime
    updated_at: datetime
    program_count: int | None = None


# --- Program ---


class CreateProgramRequest(BaseModel):
    program_name: str = Field(min_length=1, max_length=255)
    degree_type: Literal["bachelors", "masters", "phd", "certificate", "diploma"]
    school_id: UUID | None = None
    department: str | None = None
    duration_months: int | None = Field(None, ge=1, le=120)
    tuition: int | None = Field(None, ge=0)
    acceptance_rate: Decimal | None = Field(None, ge=0, le=1)
    delivery_format: Literal["in_person", "online", "hybrid"] | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    requirements: dict | None = None
    application_requirements: list[dict] | None = None
    description_text: str | None = None
    who_its_for: str | None = None
    application_deadline: date | None = None
    program_start_date: date | None = None
    # tracks/intake_rounds stored as JSONB dicts in the DB
    # (e.g., tracks = {"concentrations": [...], "note": "..."}).
    # Accept either shape for backwards-compat but the editor writes dicts.
    tracks: list | dict | None = None
    outcomes_data: dict | None = None
    intake_rounds: list | dict | None = None
    media_urls: list[str] | None = None
    highlights: list[str] | None = None
    faculty_contacts: list[dict] | None = None
    cost_data: dict | None = None
    promotion_categories: list[str] | None = None
    # Spec 38 §2.2 — English-proficiency policy for international applicants.
    english_policy: dict | None = None


class UpdateProgramRequest(BaseModel):
    program_name: str | None = Field(None, min_length=1, max_length=255)
    degree_type: Literal["bachelors", "masters", "phd", "certificate", "diploma"] | None = None
    school_id: UUID | None = None
    department: str | None = None
    # Spec 23 §6 — optimistic lock. When sent, the service rejects the write
    # with 409 if the stored feature_version has moved on (concurrent edit).
    # Control field only — popped before fields are applied to the model.
    expected_version: int | None = None
    duration_months: int | None = Field(None, ge=1, le=120)
    tuition: int | None = Field(None, ge=0)
    acceptance_rate: Decimal | None = Field(None, ge=0, le=1)
    delivery_format: Literal["in_person", "online", "hybrid"] | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    requirements: dict | None = None
    application_requirements: list[dict] | None = None
    description_text: str | None = None
    who_its_for: str | None = None
    application_deadline: date | None = None
    program_start_date: date | None = None
    # See CreateProgramRequest note — tracks/intake_rounds are JSONB dicts.
    tracks: list | dict | None = None
    outcomes_data: dict | None = None
    intake_rounds: list | dict | None = None
    media_urls: list[str] | None = None
    highlights: list[str] | None = None
    faculty_contacts: list[dict] | None = None
    cost_data: dict | None = None
    promotion_categories: list[str] | None = None
    # Spec 38 §2.2 — English-proficiency policy for international applicants.
    english_policy: dict | None = None


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    school_id: UUID | None = None
    program_name: str
    degree_type: str
    department: str | None
    duration_months: int | None
    tuition: int | None
    acceptance_rate: Decimal | None
    delivery_format: str | None = None
    campus_setting: str | None = None
    requirements: dict | None
    application_requirements: list | dict | None = None
    description_text: str | None
    who_its_for: str | None = None
    website_url: str | None = None
    class_profile: dict | None = None
    external_reviews: dict | None = None
    is_published: bool
    application_deadline: date | None
    program_start_date: date | None
    tracks: list | dict | None = None
    outcomes_data: dict | None = None
    intake_rounds: list | dict | None = None
    media_urls: list | dict | None = None
    highlights: list | dict | None
    faculty_contacts: list | dict | None = None
    cost_data: dict | None = None
    promotion_categories: list | dict | None = None
    # Spec 38 §2.2 — English-proficiency policy for international applicants.
    english_policy: dict | None = None
    # Spec 06 §5.4 — version used for cache invalidation + Spec 23 §6 optimistic
    # lock. Mapped from the model's feature_version; surfaced as `version` too.
    feature_version: int = 1
    # Spec 23 §12 — blast-radius awareness. Count of applications that reference
    # this program (set transiently by get_program; 0 on mutation responses).
    applications_count: int = 0
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def version(self) -> int:
        return self.feature_version

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> str:
        return "published" if self.is_published else "draft"


class ProgramSummaryResponse(BaseModel):
    id: UUID
    institution_id: UUID
    program_name: str
    degree_type: str
    department: str | None
    tuition: int | None
    duration_months: int | None = None
    delivery_format: str | None = None
    acceptance_rate: float | None = None
    application_deadline: date | None
    institution_name: str
    institution_country: str
    institution_city: str | None = None
    median_salary: int | None = None
    employment_rate: float | None = None
    payback_months: int | None = None
    description_text: str | None = None
    media_urls: list | dict | None = None
    highlights: list | dict | None = None
    institution_logo_url: str | None = None
    institution_image_url: str | None = None


# --- Schools ---


class SchoolSummaryResponse(BaseModel):
    id: UUID
    institution_id: UUID
    name: str
    description_text: str | None = None
    media_urls: list | dict | None = None
    logo_url: str | None = None
    website_url: str | None = None
    program_count: int = 0
    program_names: list[str] = []


# --- Target Segments ---


class CreateSegmentRequest(BaseModel):
    segment_name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    program_id: UUID | None = None
    # Spec 26 §7 — nested include/exclude rule tree; legacy flat `criteria` kept
    # optional for back-compat. The engine prefers `rules` when present.
    rules: dict | None = None
    criteria: dict | None = None
    uploaded_list_ids: list[str] = Field(default_factory=list)
    frequency_cap_per_week: int | None = Field(default=None, ge=0)
    is_active: bool = True


class UpdateSegmentRequest(BaseModel):
    segment_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    program_id: UUID | None = None
    rules: dict | None = None
    criteria: dict | None = None
    uploaded_list_ids: list[str] | None = None
    frequency_cap_per_week: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_id: UUID | None
    segment_name: str
    description: str | None = None
    rules: dict | None = None
    criteria: dict | None
    uploaded_list_ids: list[str] | None = None
    frequency_cap_per_week: int | None = None
    created_by_user_id: UUID | None = None
    preview_audience_count: int | None = None
    preview_generated_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Spec 26 §3/§7 — preview + NL bridge + signal dictionary ---


class StudentSummarySchema(BaseModel):
    student_id: str
    name: str
    email: str | None = None
    nationality: str | None = None
    country_of_residence: str | None = None
    fit_band: str | None = None


class SegmentPreviewRequest(BaseModel):
    """Preview an unsaved (or saved) rule tree (§3 'Preview audience')."""

    rules: dict | None = None
    program_id: UUID | None = None
    uploaded_list_ids: list[str] = Field(default_factory=list)


class SegmentPreviewResponse(BaseModel):
    audience_count: int
    platform_count: int
    uploaded_external_count: int
    sample: list[StudentSummarySchema]
    composition: dict[str, dict[str, int]] = Field(default_factory=dict)
    fairness_warning: str | None = None


class NLBridgeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class NLBridgeRuleSchema(BaseModel):
    field: str
    operator: str
    value: Any = None
    branch: Literal["include", "exclude"] = "include"
    ambiguous: bool = False


class NLBridgeResponse(BaseModel):
    rules: list[NLBridgeRuleSchema]
    confidence_overall: int
    ambiguity_notes: list[str] = Field(default_factory=list)


class SignalDictionaryResponse(BaseModel):
    categories: list[dict[str, Any]]
    signals: list[dict[str, Any]]


# --- Dashboard Summary ---


class PriorityQueueItem(BaseModel):
    category: str
    count: int
    deep_link: str


class DashboardSummaryResponse(BaseModel):
    program_count: int
    published_program_count: int
    total_applications: int
    pending_review_count: int
    active_events_count: int
    unread_messages_count: int
    acceptance_rate: float | None = None
    yield_rate: float | None = None
    # --- Spec 31 · Admissions Intake contract (§2 / §8) ---
    # Label for the active admissions cycle, e.g. "Fall 2027" (derived from the
    # institution's upcoming program intakes; None when no signal yet).
    cycle: str | None = None
    # Mean applicant match (fitness) score for the cycle, 0–100.
    avg_match: int | None = None
    # Conversion = admitted / decided (alias of acceptance_rate, named per §2).
    conversion_pct: float | None = None
    # Projected yield % (alias of yield_rate, named per §2).
    projected_yield_pct: float | None = None
    new_inquiries_24h: int = 0
    unanswered_inquiries_4h: int = 0
    integrity_signals_count: int = 0
    # Categorized priority queue with deep links (§2: reviewer-assignment,
    # integrity-flagged, interview-confirmations-pending).
    priority_queue: list[PriorityQueueItem] = []
    # Advisory fairness watch-point over the applicant pool (§11, G-D4/G-I5).
    fairness: dict | None = None


# --- Analytics ---


class ProgramApplicationCount(BaseModel):
    program_name: str
    count: int


class MonthlyApplicationCount(BaseModel):
    month: str
    count: int


class FunnelStage(BaseModel):
    stage: str
    count: int
    conversion_rate: float | None = None


class CampaignAttribution(BaseModel):
    campaign_id: UUID
    campaign_name: str
    recipients: int
    delivered: int
    opened: int
    clicked: int
    applications_started: int


class EventAttribution(BaseModel):
    event_id: UUID
    event_name: str
    rsvps: int
    attended: int
    applications_after: int


class AnalyticsResponse(BaseModel):
    total_applications: int
    acceptance_rate: float | None
    avg_match_score: float | None
    yield_rate: float | None
    apps_by_status: dict[str, int]
    apps_by_program: list[ProgramApplicationCount]
    apps_by_month: list[MonthlyApplicationCount]
    decisions_breakdown: dict[str, int]
    funnel_stages: list[FunnelStage] | None = None
    campaign_attribution: list[CampaignAttribution] | None = None
    event_attribution: list[EventAttribution] | None = None


# --- Campaigns (Spec 25) ---

# Spec 25 §3 enums.
CAMPAIGN_OBJECTIVES = (
    "application_open",
    "event_promotion",
    "scholarship_announcement",
    "deadline_reminder",
    "nurture",
    "general",
)
CAMPAIGN_DESTINATION_TYPES = (
    "institution_page",
    "program_page",
    "campaign_landing_page",
    "external_url",
)
CAMPAIGN_CTA_TYPES = ("learn_more", "rsvp_event", "request_info", "start_application")
CAMPAIGN_CHANNELS = ("internal_messaging", "external_email")
CAMPAIGN_STATUSES = (
    "draft",
    "pending_approval",
    "scheduled",
    "active",
    "paused",
    "completed",
)
# Spec 25 §6 attribution funnel.
ATTRIBUTION_ACTIONS = (
    "view",
    "save",
    "rsvp",
    "request_info",
    "apply_started",
    "apply_submitted",
    "decision",
)


class CampaignAudience(BaseModel):
    segment_ids: list[UUID] = Field(default_factory=list)
    uploaded_list_ids: list[UUID] = Field(default_factory=list)
    deduped_count: int | None = None


class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    objective: str | None = None
    owner_id: UUID | None = None
    associate_program_ids: list[UUID] = Field(default_factory=list)
    associate_intake_round_id: UUID | None = None
    destination_type: str | None = None
    destination_id: UUID | None = None
    destination_url: str | None = None
    cta_type: str | None = None
    channels: list[str] = Field(default_factory=list)
    audience_segment_ids: list[UUID] = Field(default_factory=list)
    audience_uploaded_list_ids: list[UUID] = Field(default_factory=list)
    subject: str | None = None
    body: str | None = None
    scheduled_at: datetime | None = None

    @field_validator("objective")
    @classmethod
    def _v_obj(cls, v: str | None) -> str | None:
        if v is not None and v not in CAMPAIGN_OBJECTIVES:
            raise ValueError(f"objective must be one of {CAMPAIGN_OBJECTIVES}")
        return v

    @field_validator("destination_type")
    @classmethod
    def _v_dest(cls, v: str | None) -> str | None:
        if v is not None and v not in CAMPAIGN_DESTINATION_TYPES:
            raise ValueError(f"destination_type must be one of {CAMPAIGN_DESTINATION_TYPES}")
        return v

    @field_validator("cta_type")
    @classmethod
    def _v_cta(cls, v: str | None) -> str | None:
        if v is not None and v not in CAMPAIGN_CTA_TYPES:
            raise ValueError(f"cta_type must be one of {CAMPAIGN_CTA_TYPES}")
        return v

    @field_validator("channels")
    @classmethod
    def _v_channels(cls, v: list[str]) -> list[str]:
        for c in v:
            if c not in CAMPAIGN_CHANNELS:
                raise ValueError(f"channel must be one of {CAMPAIGN_CHANNELS}")
        return v


class UpdateCampaignRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    objective: str | None = None
    owner_id: UUID | None = None
    associate_program_ids: list[UUID] | None = None
    associate_intake_round_id: UUID | None = None
    destination_type: str | None = None
    destination_id: UUID | None = None
    destination_url: str | None = None
    cta_type: str | None = None
    channels: list[str] | None = None
    audience_segment_ids: list[UUID] | None = None
    audience_uploaded_list_ids: list[UUID] | None = None
    subject: str | None = None
    body: str | None = None
    scheduled_at: datetime | None = None

    @field_validator("objective")
    @classmethod
    def _v_obj(cls, v: str | None) -> str | None:
        if v is not None and v not in CAMPAIGN_OBJECTIVES:
            raise ValueError(f"objective must be one of {CAMPAIGN_OBJECTIVES}")
        return v

    @field_validator("destination_type")
    @classmethod
    def _v_dest(cls, v: str | None) -> str | None:
        if v is not None and v not in CAMPAIGN_DESTINATION_TYPES:
            raise ValueError(f"destination_type must be one of {CAMPAIGN_DESTINATION_TYPES}")
        return v

    @field_validator("cta_type")
    @classmethod
    def _v_cta(cls, v: str | None) -> str | None:
        if v is not None and v not in CAMPAIGN_CTA_TYPES:
            raise ValueError(f"cta_type must be one of {CAMPAIGN_CTA_TYPES}")
        return v

    @field_validator("channels")
    @classmethod
    def _v_channels(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for c in v:
            if c not in CAMPAIGN_CHANNELS:
                raise ValueError(f"channel must be one of {CAMPAIGN_CHANNELS}")
        return v


class RejectCampaignRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


class CampaignMetrics(BaseModel):
    sent: int = 0
    delivered: int = 0
    opens: int = 0
    clicks: int = 0
    conversions: dict[str, int] = Field(default_factory=dict)
    unsubscribes: int = 0
    bounces: int = 0


class CampaignResponse(BaseModel):
    id: UUID
    institution_id: UUID
    name: str
    objective: str | None = None
    owner_id: UUID | None = None
    status: str
    associate_program_ids: list[UUID] = Field(default_factory=list)
    associate_intake_round_id: UUID | None = None
    destination_type: str | None = None
    destination_id: UUID | None = None
    destination_url: str | None = None
    cta_type: str | None = None
    channels: list[str] = Field(default_factory=list)
    audience: CampaignAudience
    subject: str | None = None
    body: str | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    sent_count: int | None = None
    metrics: CampaignMetrics | None = None
    submitted_for_approval_at: datetime | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejection_comment: str | None = None
    requires_approval: bool = False
    created_at: datetime
    updated_at: datetime


class CampaignMetricsResponse(CampaignMetrics):
    """Spec 25 §8 metrics shape, plus the campaign id for convenience."""

    campaign_id: UUID


# --- Campaign Links & Attribution ---


class CreateCampaignLinkRequest(BaseModel):
    destination_type: str = Field(
        ...,
        pattern=r"^(program|institution|event|post|custom)$",
    )
    destination_id: UUID | None = None
    custom_url: str | None = None
    label: str | None = None


class CampaignLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    campaign_id: UUID
    institution_id: UUID
    destination_type: str
    destination_id: UUID | None
    custom_url: str | None
    short_code: str
    label: str | None
    click_count: int
    trackable_url: str | None = None
    destination_name: str | None = None
    created_at: datetime


class LinkPerformance(BaseModel):
    link_id: UUID
    label: str | None
    destination_name: str | None
    clicks: int
    views: int
    saves: int
    applications: int


class CampaignAttributionDetail(BaseModel):
    campaign_id: UUID
    campaign_name: str
    recipients: int
    delivered: int
    opened: int
    clicked: int
    views: int
    saves: int
    rsvps: int
    request_infos: int
    applications: int
    links: list[LinkPerformance]


class RecordActionRequest(BaseModel):
    campaign_id: UUID
    action_type: str = Field(
        ...,
        # Spec 25 §6 funnel (+ legacy 'apply' alias for apply_started).
        pattern=r"^(view|save|rsvp|request_info|apply|apply_started|apply_submitted|decision)$",
    )
    target_id: UUID | None = None
    link_id: UUID | None = None


# --- Campaign audience preview (Spec 25 §8 preview-audience) ---


class AudienceSamplePerson(BaseModel):
    student_id: UUID | None = None
    name: str | None = None
    email: str | None = None
    source: str  # 'platform' | 'uploaded_list'
    channel: str  # 'internal' | 'external'


class AudiencePreviewResponse(BaseModel):
    campaign_id: UUID | None = None
    deduped_count: int
    platform_count: int = 0
    uploaded_count: int = 0
    suppressed_count: int = 0
    consent_excluded_count: int = 0
    sample: list[AudienceSamplePerson] = Field(default_factory=list)


# --- Uploaded contact lists (Spec 24/26 §2.5) ---


class CreateUploadedListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    source: str = Field(default="csv_upload", max_length=30)
    source_consent_confirmed: bool = False
    # Inline CSV-style rows: list of {email, first_name?, last_name?, ...}
    contacts: list[dict] = Field(default_factory=list)


class UpdateUploadedListRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    source_consent_confirmed: bool | None = None


class UploadedListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    name: str
    description: str | None = None
    source: str
    source_consent_confirmed: bool
    contact_count: int
    created_at: datetime
    updated_at: datetime


# --- Suppression list (Spec 25 §4 / 46) ---


class CreateSuppressionRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    reason: str | None = Field(default="manual", max_length=30)


class SuppressionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    email: str
    reason: str | None = None
    created_at: datetime


# --- AI: CampaignAudienceCopySuggester (Spec 45 §16) ---


class DraftCampaignCopyRequest(BaseModel):
    objective: str | None = None
    cta_type: str | None = None
    audience_summary: str | None = Field(default=None, max_length=2000)
    audience_segment_ids: list[UUID] = Field(default_factory=list)
    tone: str | None = Field(default=None, max_length=120)
    additional_context: str | None = Field(default=None, max_length=2000)


class DraftCampaignCopyResponse(BaseModel):
    subject: str
    body: str
    alternate_subjects: list[str] = Field(default_factory=list)
    preview_text: str = ""
    source: str = "llm"  # 'llm' | 'fallback'
    disabled: bool = False
    # Spec 37 §3 — token to thread back on save so the human edit diff is captured.
    draft_token: str | None = None


class RecordEngagementRequest(BaseModel):
    """Spec 27 §5 — a per-object engagement event from a student surface."""

    object_type: Literal["post", "event", "promotion"]
    object_id: UUID
    action: Literal["view", "impression", "click", "save", "request_info", "apply_started"]


# --- Inquiries ---


class SubmitInquiryRequest(BaseModel):
    institution_id: UUID
    program_id: UUID | None = None
    subject: str = Field(min_length=1, max_length=500)
    message: str = Field(min_length=1, max_length=5000)
    inquiry_type: str = "general"
    campaign_id: UUID | None = None


class UpdateInquiryRequest(BaseModel):
    status: str | None = Field(
        None,
        pattern=r"^(new|in_progress|responded|closed)$",
    )
    assigned_to: UUID | None = None
    response_text: str | None = None


class InquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_id: UUID | None
    student_id: UUID | None
    student_name: str
    student_email: str
    subject: str
    message: str
    inquiry_type: str
    status: str
    assigned_to: UUID | None
    response_text: str | None
    responded_at: datetime | None
    campaign_id: UUID | None
    created_at: datetime
    updated_at: datetime
    program_name: str | None = None


class InquiryRoutingConfig(BaseModel):
    """Institution's inquiry routing preferences."""

    default_email: str | None = None
    auto_reply_enabled: bool = False
    auto_reply_message: str | None = None
    forward_to_email: bool = True
    inquiry_types: list[str] | None = None


# --- Promotions ---


class TargetingScope(BaseModel):
    regions: list[str] | None = None
    countries: list[str] | None = None
    degree_types: list[str] | None = None
    interests: list[str] | None = None


class CreatePromotionRequest(BaseModel):
    program_id: UUID | None = None
    promotion_type: str = Field(
        "spotlight",
        pattern=r"^(spotlight|featured|banner)$",
    )
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    targeting: TargetingScope | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    # Spec 27 §4.1 — target a program (default), the institution, or a landing URL.
    target_kind: Literal["program", "institution", "landing"] = "program"
    target_url: str | None = Field(None, max_length=1000)


class UpdatePromotionRequest(BaseModel):
    program_id: UUID | None = None
    promotion_type: str | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    targeting: TargetingScope | None = None
    status: str | None = Field(
        None,
        pattern=r"^(draft|scheduled|active|paused|expired)$",
    )
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    target_kind: Literal["program", "institution", "landing"] | None = None
    target_url: str | None = Field(None, max_length=1000)


class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_id: UUID | None
    promotion_type: str
    title: str
    description: str | None
    targeting: dict | None
    status: str
    starts_at: datetime | None
    ends_at: datetime | None
    impression_count: int
    click_count: int
    target_kind: str = "program"
    target_url: str | None = None
    created_at: datetime
    updated_at: datetime
    program_name: str | None = None
    institution_name: str | None = None
    is_eligible: bool = True


# --- Datasets ---


class CreateDatasetRequest(BaseModel):
    dataset_name: str = Field(min_length=1, max_length=255)
    dataset_type: Literal["admissions_history", "prospect_list", "outcomes_summary"]
    description: str | None = None
    file_name: str = Field(min_length=1)
    content_type: str = "text/csv"
    file_size_bytes: int | None = None
    usage_scope: Literal["marketing", "analytics", "admissions", "all"] | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None
    update_mode: Literal["replace", "append"] = "replace"


class ConfirmDatasetRequest(BaseModel):
    column_mapping: dict[str, str] | None = None
    skip_invalid_rows: bool = False
    save_template: bool = False
    template_name: str | None = None


class DatasetReplaceRequest(BaseModel):
    file_name: str = Field(min_length=1)
    content_type: str = "text/csv"
    file_size_bytes: int | None = None


class ConfirmDatasetReplaceRequest(BaseModel):
    staging_s3_key: str
    file_name: str = Field(min_length=1)
    update_mode: Literal["replace", "append"] = "replace"
    column_mapping: dict[str, str] | None = None
    skip_invalid_rows: bool = False


class UpdateDatasetRequest(BaseModel):
    dataset_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    column_mapping: dict | None = None
    usage_scope: str | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None
    status: (
        Literal["uploaded", "validated", "processed", "failed", "pending", "active", "archived"]
        | None
    ) = None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    dataset_name: str
    dataset_type: str
    description: str | None
    file_name: str
    file_size_bytes: int | None
    row_count: int | None
    column_mapping: dict | None
    validation_errors: list | dict | None = None
    status: str
    usage_scope: str | None
    coverage_start: date | None = None
    coverage_end: date | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    download_url: str | None = None
    used_by: list[str] = []


class DatasetUploadResponse(BaseModel):
    dataset_id: UUID
    upload_url: str
    staging_s3_key: str | None = None


class DatasetPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict]
    total_rows: int
    column_histogram: dict[str, dict[str, int]] = {}


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    dataset_id: UUID
    version_number: int
    row_count: int | None
    changes_summary: dict | None
    validation_report: dict | None
    uploaded_at: datetime


class DatasetMappingTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    name: str
    dataset_type: str
    column_mapping: dict
    created_at: datetime
    updated_at: datetime


class SaveMappingTemplateRequest(BaseModel):
    template_name: str = Field(min_length=1, max_length=255)
    dataset_type: Literal["admissions_history", "prospect_list", "outcomes_summary"]
    column_mapping: dict[str, str]


# --- Posts ---


class PostCTA(BaseModel):
    """Spec 27 §2.4 — a call-to-action attached to a post."""

    type: Literal[
        "view_program",
        "rsvp",
        "request_info",
        "start_application",
        "add_to_calendar",
    ]
    label: str = Field(min_length=1, max_length=80)
    # program_id / event_id / url depending on type; optional for institution-wide.
    target: str | None = None


class PostVisibility(BaseModel):
    """Spec 27 §2.3 — visibility scope for a post."""

    public: bool = True
    segment_ids: list[UUID] = Field(default_factory=list)
    region_scopes: list[str] = Field(default_factory=list)


class CreatePostRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    media_urls: list[dict] | None = None
    tagged_program_ids: list[UUID] | None = None
    tagged_intake: str | None = None
    status: Literal["draft", "published", "scheduled"] = "draft"
    scheduled_for: datetime | None = None
    is_template: bool = False
    template_name: str | None = None
    ctas: list[PostCTA] | None = None
    visibility: PostVisibility | None = None


class UpdatePostRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    body: str | None = Field(None, min_length=1)
    media_urls: list[dict] | None = None
    tagged_program_ids: list[UUID] | None = None
    tagged_intake: str | None = None
    status: Literal["draft", "published", "scheduled", "archived"] | None = None
    scheduled_for: datetime | None = None
    is_template: bool | None = None
    template_name: str | None = None
    ctas: list[PostCTA] | None = None
    visibility: PostVisibility | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    author_id: UUID | None
    title: str
    body: str
    media_urls: list | dict | None = None
    pinned: bool
    tagged_program_ids: list | dict | None = None
    tagged_intake: str | None
    status: str
    scheduled_for: datetime | None
    published_at: datetime | None
    is_template: bool
    template_name: str | None
    view_count: int
    # Spec 27 §5 — per-object engagement counters.
    click_count: int = 0
    save_count: int = 0
    request_info_count: int = 0
    apply_started_count: int = 0
    # Spec 27 §2.4 / §2.3 — CTAs + visibility scope (raw JSONB passthrough).
    ctas: list | None = None
    visibility: dict | None = None
    created_at: datetime
    updated_at: datetime
    author_email: str | None = None
    program_names: list[str] | None = None


class PostMediaUploadResponse(BaseModel):
    upload_url: str
    media_key: str


# --- NLP Search ---


class NLPSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class NLPSearchResponse(BaseModel):
    filters_applied: dict
    results: PaginatedResponse[ProgramSummaryResponse]
    interpretation: str
