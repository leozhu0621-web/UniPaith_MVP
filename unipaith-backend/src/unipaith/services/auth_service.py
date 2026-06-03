import logging
import uuid
from typing import Any

import boto3
import httpx
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, ConflictException
from unipaith.core.security import CognitoClaims
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

logger = logging.getLogger("unipaith.auth")


def _get_cognito_client():  # type: ignore[no-untyped-def]
    kwargs: dict = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("cognito-idp", **kwargs)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, email: str, password: str, role: str) -> dict[str, Any]:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ConflictException("Email already registered")

        cognito_sub = str(uuid.uuid4())

        if not settings.cognito_bypass:
            client = _get_cognito_client()
            try:
                resp = client.sign_up(
                    ClientId=settings.cognito_app_client_id,
                    Username=email,
                    Password=password,
                    UserAttributes=[
                        {"Name": "email", "Value": email},
                        {"Name": "name", "Value": email.split("@")[0]},
                    ],
                )
                cognito_sub = resp["UserSub"]
                client.admin_confirm_sign_up(
                    UserPoolId=settings.cognito_user_pool_id,
                    Username=email,
                )
            except client.exceptions.UsernameExistsException:
                raise ConflictException("Email already registered in Cognito")  # noqa: B904
            except Exception as e:
                raise BadRequestException(f"Cognito signup failed: {e}") from e
        else:
            cognito_sub = f"dev-sub-{email.split('@')[0]}"

        user = User(email=email, cognito_sub=cognito_sub, role=UserRole(role))
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        if role == "student":
            profile = StudentProfile(user_id=user.id)
            self.db.add(profile)
            await self.db.flush()
        return {"user_id": user.id, "email": user.email, "role": user.role.value}

    async def login(self, email: str, password: str) -> dict[str, Any]:
        if settings.cognito_bypass:
            user_result = await self.db.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()
            if not user:
                raise BadRequestException("Invalid credentials")
            if settings.demo_mode and user.role.value == "student":
                from unipaith.services.demo_service import reset_student_demo_data

                await reset_student_demo_data(self.db, user.id)
            return {
                "access_token": f"dev:{user.id}:{user.role.value}",
                "refresh_token": f"dev-refresh:{user.id}",
                "expires_in": 3600,
                "token_type": "Bearer",
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role.value,
                    "created_at": user.created_at,
                },
            }

        client = _get_cognito_client()
        try:
            resp = client.initiate_auth(
                ClientId=settings.cognito_app_client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password},
            )
            auth_result = resp["AuthenticationResult"]
            user_result = await self.db.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()
            if not user:
                raise BadRequestException(
                    "No application account for this email. Please sign up first."
                )
            # Sync cognito_sub from the token so /auth/me lookups work
            id_token = auth_result.get("IdToken")
            if id_token:
                try:
                    claims = jwt.get_unverified_claims(id_token)
                    token_sub = claims.get("sub")
                    if token_sub and user.cognito_sub != token_sub:
                        user.cognito_sub = token_sub
                        await self.db.flush()
                except Exception:
                    pass  # Non-critical — login still succeeds
            if settings.demo_mode and user.role.value == "student":
                from unipaith.services.demo_service import reset_student_demo_data

                await reset_student_demo_data(self.db, user.id)
            return {
                "access_token": auth_result.get("IdToken", auth_result["AccessToken"]),
                "refresh_token": auth_result.get("RefreshToken"),
                "expires_in": auth_result["ExpiresIn"],
                "token_type": "Bearer",
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role.value,
                    "created_at": user.created_at,
                },
            }
        except BadRequestException:
            raise
        except Exception as e:
            # Sanitize error responses for the login endpoint. The raw
            # exception text can include sensitive infrastructure details
            # (DB usernames, asyncpg password-auth errors, AWS SDK wraps
            # with API call shapes, etc.) — none of which the user can
            # act on. Cognito's NotAuthorizedException is the only error
            # the user CAN act on, so we map it to a clear bad-credentials
            # message; everything else surfaces as a generic 503-style
            # message and gets logged server-side.
            err_class = type(e).__name__
            err_str = str(e)
            if "NotAuthorizedException" in err_class or "NotAuthorizedException" in err_str:
                raise BadRequestException("Incorrect email or password.") from e
            if "UserNotFoundException" in err_class or "UserNotFoundException" in err_str:
                raise BadRequestException(
                    "No account with that email. Please sign up first."
                ) from e
            if "UserNotConfirmedException" in err_class or "UserNotConfirmedException" in err_str:
                raise BadRequestException(
                    "Your account isn't confirmed yet — check your email for the verification link."
                ) from e
            # Anything else: log the real cause server-side, return a
            # generic message to the client. logger captures the type +
            # message; full traceback is available in CloudWatch via the
            # structured exception handler.
            logger.exception("Login failed for %s with unexpected error", email)
            raise BadRequestException(
                "We're having trouble signing you in right now. Please try again in a moment."
            ) from e

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        if settings.cognito_bypass:
            parts = refresh_token.split(":")
            user_id = parts[1] if len(parts) > 1 else None
            if user_id:
                result = await self.db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                role = user.role.value if user else "student"
            else:
                role = "student"
            return {
                "access_token": f"dev:{user_id or 'unknown'}:{role}",
                "expires_in": 3600,
                "token_type": "Bearer",
            }

        client = _get_cognito_client()
        try:
            resp = client.initiate_auth(
                ClientId=settings.cognito_app_client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": refresh_token},
            )
            auth_result = resp["AuthenticationResult"]
            return {
                "access_token": auth_result.get("IdToken", auth_result["AccessToken"]),
                "expires_in": auth_result.get("ExpiresIn", 3600),
                "token_type": "Bearer",
            }
        except Exception as e:
            raise BadRequestException(f"Token refresh failed: {e}") from e

    async def google_callback(
        self, code: str, redirect_uri: str, role: str = "student"
    ) -> dict[str, Any]:
        """Exchange a Cognito authorization code for tokens, find/create user."""
        token_endpoint = f"https://{settings.cognito_domain}/oauth2/token"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    token_endpoint,
                    data={
                        "grant_type": "authorization_code",
                        "client_id": settings.cognito_app_client_id,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if resp.status_code != 200:
                    logger.error("Cognito token exchange failed: %s", resp.status_code)
                    raise BadRequestException(f"Token exchange failed: {resp.text}")
                tokens = resp.json()
        except httpx.HTTPError as e:
            raise BadRequestException(f"Token exchange request failed: {e}") from e

        # Decode the ID token (without verification — Cognito already validated it)
        id_token = tokens.get("id_token", "")
        try:
            claims = jwt.get_unverified_claims(id_token)
        except Exception as e:
            raise BadRequestException(f"Failed to decode ID token: {e}") from e

        cognito_sub = claims.get("sub", "")
        email = claims.get("email", "")
        if not email:
            raise BadRequestException("Google account has no email")

        # Find existing user by cognito_sub or email
        result = await self.db.execute(
            select(User).where((User.cognito_sub == cognito_sub) | (User.email == email))
        )
        user = result.scalar_one_or_none()

        if user is None:
            # First-time Google sign-in — create account
            user = User(
                email=email,
                cognito_sub=cognito_sub,
                role=UserRole(role),
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)

            if role == "student":
                self.db.add(StudentProfile(user_id=user.id))
                await self.db.flush()

            logger.info("Created new user via Google: %s (%s)", email, role)
        else:
            # Update cognito_sub if user was created via email/password before
            if user.cognito_sub != cognito_sub:
                user.cognito_sub = cognito_sub
                await self.db.flush()

        return {
            "access_token": tokens.get("id_token", tokens["access_token"]),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in", 3600),
            "token_type": "Bearer",
            "user": {
                "user_id": user.id,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at,
            },
        }

    async def google_signin(self, id_token_str: str, role: str = "student") -> dict[str, Any]:
        """Verify a Google ID token (GIS-direct) and find/create the student, then
        issue the app session token. Demo/bypass path; requires
        ``settings.google_client_id``. Prod federated sign-in stays on
        ``google_callback`` (Cognito hosted UI)."""
        if not settings.google_client_id:
            raise BadRequestException("Google sign-in is not configured")

        try:
            # Parse the header first (no network) so a malformed token fails fast.
            header = jwt.get_unverified_header(id_token_str)
            async with httpx.AsyncClient(timeout=10.0) as client:
                certs = (await client.get("https://www.googleapis.com/oauth2/v3/certs")).json()
            key = next(
                (k for k in certs.get("keys", []) if k.get("kid") == header.get("kid")), None
            )
            if key is None:
                raise BadRequestException("Unknown Google signing key")
            claims = jwt.decode(
                id_token_str,
                key,
                algorithms=["RS256"],
                audience=settings.google_client_id,
                options={"verify_at_hash": False},
            )
        except BadRequestException:
            raise
        except Exception as e:
            raise BadRequestException(f"Invalid Google token: {e}") from e

        if claims.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
            raise BadRequestException("Invalid Google token issuer")
        email = claims.get("email", "")
        google_sub = claims.get("sub", "")
        if not email:
            raise BadRequestException("Google account has no email")

        result = await self.db.execute(
            select(User).where((User.cognito_sub == google_sub) | (User.email == email))
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=email, cognito_sub=google_sub, role=UserRole(role))
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
            if role == "student":
                self.db.add(StudentProfile(user_id=user.id))
                await self.db.flush()
            logger.info("Created new user via Google sign-in: %s (%s)", email, role)
        elif not user.cognito_sub:
            user.cognito_sub = google_sub
            await self.db.flush()

        if settings.demo_mode and user.role.value == "student":
            from unipaith.services.demo_service import reset_student_demo_data

            await reset_student_demo_data(self.db, user.id)

        return {
            "access_token": f"dev:{user.id}:{user.role.value}",
            "refresh_token": f"dev-refresh:{user.id}",
            "expires_in": 3600,
            "token_type": "Bearer",
            "user": {
                "user_id": user.id,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at,
            },
        }

    async def get_or_create_user(self, claims: CognitoClaims) -> User:
        result = await self.db.execute(select(User).where(User.cognito_sub == claims.sub))
        user = result.scalar_one_or_none()
        if user:
            return user

        user = User(email=claims.email, cognito_sub=claims.sub, role=UserRole(claims.role))
        self.db.add(user)
        await self.db.flush()
        if claims.role == "student":
            profile = StudentProfile(user_id=user.id)
            self.db.add(profile)
            await self.db.flush()
        return user
