"""Communication template service — CRUD, personalization, and delivery."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.models.application import Application
from unipaith.models.institution import (
    CommunicationTemplate,
    Institution,
    Program,
)
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.schemas.communication import (
    CreateTemplateRequest,
    SendResult,
    TemplatePreviewResponse,
    TemplateResponse,
    UpdateTemplateRequest,
)


def _personalize(template: str, variables: dict[str, str]) -> str:
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", value or "")
    return result


def _extract_variables(text: str) -> list[str]:
    return list(set(re.findall(r"\{\{(\w+)\}\}", text)))


class CommunicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_templates(
        self,
        institution_id: UUID,
        template_type: str | None = None,
        program_id: UUID | None = None,
    ) -> list[TemplateResponse]:
        stmt = (
            select(CommunicationTemplate)
            .where(CommunicationTemplate.institution_id == institution_id)
            .order_by(CommunicationTemplate.template_type, CommunicationTemplate.name)
        )
        if template_type:
            stmt = stmt.where(CommunicationTemplate.template_type == template_type)
        if program_id:
            stmt = stmt.where(CommunicationTemplate.program_id == program_id)
        result = await self.db.execute(stmt)
        return [await self._enrich(t) for t in result.scalars().all()]

    async def create_template(
        self,
        institution_id: UUID,
        data: CreateTemplateRequest,
    ) -> TemplateResponse:
        # If setting as default, unset existing default of same type
        if data.is_default:
            await self._unset_defaults(institution_id, data.template_type)

        tmpl = CommunicationTemplate(
            institution_id=institution_id,
            program_id=data.program_id,
            template_type=data.template_type,
            name=data.name,
            subject=data.subject,
            body=data.body,
            variables=data.variables
            or _extract_variables(
                data.subject + " " + data.body,
            ),
            is_default=data.is_default,
        )
        self.db.add(tmpl)
        await self.db.flush()
        await self.db.refresh(tmpl)
        return await self._enrich(tmpl)

    async def update_template(
        self,
        institution_id: UUID,
        template_id: UUID,
        data: UpdateTemplateRequest,
    ) -> TemplateResponse:
        tmpl = await self._get(institution_id, template_id)
        update = data.model_dump(exclude_unset=True)

        if update.get("is_default"):
            ttype = update.get("template_type", tmpl.template_type)
            await self._unset_defaults(institution_id, ttype)

        for key, val in update.items():
            setattr(tmpl, key, val)

        # Re-extract variables if subject/body changed
        if "subject" in update or "body" in update:
            tmpl.variables = _extract_variables(
                tmpl.subject + " " + tmpl.body,
            )

        await self.db.flush()
        await self.db.refresh(tmpl)
        return await self._enrich(tmpl)

    async def delete_template(
        self,
        institution_id: UUID,
        template_id: UUID,
    ) -> None:
        tmpl = await self._get(institution_id, template_id)
        await self.db.delete(tmpl)
        await self.db.flush()

    async def preview_template(
        self,
        institution_id: UUID,
        template_id: UUID,
        application_id: UUID | None = None,
    ) -> TemplatePreviewResponse:
        tmpl = await self._get(institution_id, template_id)
        variables = await self._resolve_variables(
            institution_id,
            application_id,
        )
        return TemplatePreviewResponse(
            rendered_subject=_personalize(tmpl.subject, variables),
            rendered_body=_personalize(tmpl.body, variables),
            variables_used=list(variables.keys()),
        )

    async def send_from_template(
        self,
        institution_id: UUID,
        actor_user_id: UUID,
        template_id: UUID,
        application_ids: list[UUID],
        overrides: dict[str, str] | None = None,
    ) -> SendResult:
        from unipaith.services.notification_service import NotificationService

        tmpl = await self._get(institution_id, template_id)
        notif_svc = NotificationService(self.db)
        success = 0
        failed: list[UUID] = []

        for app_id in application_ids:
            try:
                variables = await self._resolve_variables(
                    institution_id,
                    app_id,
                )
                if overrides:
                    variables.update(overrides)

                subject = _personalize(tmpl.subject, variables)
                body = _personalize(tmpl.body, variables)

                # Get student user_id
                r = await self.db.execute(
                    select(Application.student_id).where(
                        Application.id == app_id,
                    )
                )
                student_profile_id = r.scalar_one_or_none()
                if not student_profile_id:
                    failed.append(app_id)
                    continue

                ur = await self.db.execute(
                    select(StudentProfile.user_id).where(
                        StudentProfile.id == student_profile_id,
                    )
                )
                user_id = ur.scalar_one_or_none()
                if not user_id:
                    failed.append(app_id)
                    continue

                await notif_svc.notify(
                    user_id=user_id,
                    notification_type=f"template_{tmpl.template_type}",
                    title=subject,
                    body=body,
                    action_url="/s/messages",
                    metadata={
                        "template_id": str(template_id),
                        "application_id": str(app_id),
                    },
                )
                success += 1
            except Exception:
                failed.append(app_id)

        return SendResult(success_count=success, failed_ids=failed)

    # --- Helpers ---

    async def _get(
        self,
        institution_id: UUID,
        template_id: UUID,
    ) -> CommunicationTemplate:
        r = await self.db.execute(
            select(CommunicationTemplate).where(
                CommunicationTemplate.id == template_id,
                CommunicationTemplate.institution_id == institution_id,
            )
        )
        tmpl = r.scalar_one_or_none()
        if not tmpl:
            raise NotFoundException("Template not found")
        return tmpl

    async def _unset_defaults(
        self,
        institution_id: UUID,
        template_type: str,
    ) -> None:
        from sqlalchemy import update

        await self.db.execute(
            update(CommunicationTemplate)
            .where(
                CommunicationTemplate.institution_id == institution_id,
                CommunicationTemplate.template_type == template_type,
                CommunicationTemplate.is_default.is_(True),
            )
            .values(is_default=False)
        )

    async def _resolve_variables(
        self,
        institution_id: UUID,
        application_id: UUID | None,
    ) -> dict[str, str]:
        """Resolve personalization variables from application context."""
        variables: dict[str, str] = {}

        # Institution info
        ir = await self.db.execute(select(Institution).where(Institution.id == institution_id))
        inst = ir.scalar_one_or_none()
        if inst:
            variables["institution_name"] = inst.name

        if not application_id:
            variables.setdefault("first_name", "Student")
            variables.setdefault("last_name", "")
            variables.setdefault("program_name", "Program")
            variables.setdefault("email", "student@example.com")
            return variables

        # Application + student + program
        ar = await self.db.execute(select(Application).where(Application.id == application_id))
        app = ar.scalar_one_or_none()
        if app:
            # Program
            pr = await self.db.execute(
                select(Program.program_name).where(
                    Program.id == app.program_id,
                )
            )
            variables["program_name"] = pr.scalar_one_or_none() or "Program"

            # Student
            sr = await self.db.execute(
                select(StudentProfile).where(
                    StudentProfile.id == app.student_id,
                )
            )
            student = sr.scalar_one_or_none()
            if student:
                variables["first_name"] = student.first_name or ""
                variables["last_name"] = student.last_name or ""
                # Get email from user
                eur = await self.db.execute(
                    select(User.email).where(
                        User.id == student.user_id,
                    )
                )
                variables["email"] = eur.scalar_one_or_none() or ""

        return variables

    async def _enrich(
        self,
        tmpl: CommunicationTemplate,
    ) -> TemplateResponse:
        prog_name = None
        if tmpl.program_id:
            r = await self.db.execute(
                select(Program.program_name).where(
                    Program.id == tmpl.program_id,
                )
            )
            prog_name = r.scalar_one_or_none()

        return TemplateResponse(
            id=tmpl.id,
            institution_id=tmpl.institution_id,
            program_id=tmpl.program_id,
            template_type=tmpl.template_type,
            name=tmpl.name,
            subject=tmpl.subject,
            body=tmpl.body,
            variables=tmpl.variables,
            is_default=tmpl.is_default,
            is_active=tmpl.is_active,
            created_at=tmpl.created_at,
            updated_at=tmpl.updated_at,
            program_name=prog_name,
        )

    # --- AI Draft Generation ---

    async def generate_ai_draft(
        self,
        institution_id: UUID,
        application_id: UUID,
        message_type: str,
        context_notes: str | None = None,
    ) -> dict:
        """Generate a context-aware message draft using AI."""
        import json

        from unipaith.ai.llm_client import get_llm_client

        variables = await self._resolve_variables(
            institution_id,
            application_id,
        )

        # Load application context for richer drafts
        app_context = {}
        ar = await self.db.execute(select(Application).where(Application.id == application_id))
        app = ar.scalar_one_or_none()
        if app:
            app_context = {
                "status": app.status,
                "decision": app.decision,
                "completeness": app.completeness_status,
                "missing_items": app.missing_items,
            }

        # Get institution name
        ir = await self.db.execute(
            select(Institution.name).where(
                Institution.id == institution_id,
            )
        )
        inst_name = ir.scalar_one_or_none() or "Institution"

        type_instructions = {
            "missing_items": (
                "Write a polite, professional email requesting the "
                "student submit missing application materials. "
                "Be specific about what's missing based on the context."
            ),
            "interview_invite": (
                "Write a warm, professional interview invitation. "
                "Express interest in the applicant and provide "
                "logistical details placeholder."
            ),
            "clarification": (
                "Write a professional email requesting clarification "
                "on specific aspects of the application. Be clear "
                "about what needs to be clarified."
            ),
            "decision_admit": (
                "Write a congratulatory admission letter. Express "
                "enthusiasm about the student joining the program."
            ),
            "decision_reject": (
                "Write a respectful, encouraging rejection letter. "
                "Thank the student for their interest and wish them "
                "well in their future endeavors."
            ),
            "decision_waitlist": (
                "Write an informative waitlist notification. Explain the process and timeline."
            ),
            "offer_notice": (
                "Write a formal offer letter with financial details "
                "placeholder and response deadline."
            ),
        }

        instruction = type_instructions.get(
            message_type,
            "Write a professional email for the admissions context.",
        )

        system_prompt = (
            f"You are writing on behalf of {inst_name} admissions. "
            f"{instruction} "
            "Respond in JSON with keys: "
            '"subject" (email subject line) and "body" (email body). '
            "Use the student's first name. Be professional but warm. "
            "Keep it concise (under 200 words for body)."
        )

        user_content = (
            f"Student: {variables.get('first_name', '')} "
            f"{variables.get('last_name', '')}\n"
            f"Program: {variables.get('program_name', '')}\n"
            f"Application status: {app_context.get('status', 'N/A')}\n"
            f"Completeness: {app_context.get('completeness', 'N/A')}\n"
        )
        if app_context.get("missing_items"):
            user_content += f"Missing items: {json.dumps(app_context['missing_items'])}\n"
        if app_context.get("decision"):
            user_content += f"Decision: {app_context['decision']}\n"
        if context_notes:
            user_content += f"Additional context: {context_notes}\n"

        llm = get_llm_client()
        raw = await llm.generate_reasoning(system_prompt, user_content)

        try:
            data = json.loads(raw)
            return {
                "subject": data.get("subject", ""),
                "body": data.get("body", ""),
                "message_type": message_type,
                "variables_used": variables,
                "editable": True,
            }
        except (json.JSONDecodeError, TypeError):
            return {
                "subject": (
                    f"Regarding your application to {variables.get('program_name', 'our program')}"
                ),
                "body": raw or "Draft generation failed.",
                "message_type": message_type,
                "variables_used": variables,
                "editable": True,
            }
