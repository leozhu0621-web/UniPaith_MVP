# Task 03: Authentication — Amazon Cognito Integration

## Context

You are building auth for **UniPaith**, an AI-powered admissions platform. Tasks 01-02 set up the project scaffolding and database schema. Now add authentication using Amazon Cognito.

**Architecture decision:** Cognito handles user registration, login, password reset, and token issuance. Our backend **verifies** Cognito JWT tokens — it does NOT store passwords.

## What to Build

### 1. AWS Cognito Setup Script

Create `scripts/setup_cognito.py` — a one-time script that creates the Cognito User Pool and App Client using boto3. This is run manually during infrastructure setup, not at runtime.

```python
"""
Run once to create Cognito User Pool and App Client.
Outputs the pool_id and client_id to add to .env
"""
```

The script should create:
- **User Pool** named "unipaith-users" with:
  - Email as the username attribute
  - Email verification enabled (auto-verify for MVP)
  - Password policy: minimum 8 chars, require uppercase, lowercase, number
  - Custom attributes: `custom:role` (string: "student" or "institution_admin")
- **App Client** named "unipaith-api" with:
  - ALLOW_USER_PASSWORD_AUTH and ALLOW_REFRESH_TOKEN_AUTH flows
  - No client secret (for public client / SPA)
  - Token validity: access token 1 hour, refresh token 30 days

Print the `user_pool_id` and `app_client_id` at the end so they can be added to `.env`.

### 2. core/security.py — Token Verification

Implement JWT verification that:

1. Fetches Cognito's JWKS (JSON Web Key Set) from `https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`
2. Caches the JWKS in memory (refresh every 24 hours)
3. Verifies the JWT signature, expiration, audience, and issuer
4. Extracts claims: `sub` (Cognito user ID), `email`, `custom:role`

```python
# Public interface:
async def verify_token(token: str) -> CognitoClaims:
    """Verify a Cognito JWT and return parsed claims. Raises HTTPException(401) on failure."""

class CognitoClaims(BaseModel):
    sub: str           # Cognito user ID
    email: str
    role: str          # from custom:role
```

Use `python-jose` for JWT verification. Fetch JWKS using `httpx.AsyncClient`.

### 3. dependencies.py — Auth Dependencies

Create FastAPI dependencies for route protection:

```python
async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract Bearer token from Authorization header.
    Verify with Cognito. Look up user in our DB.
    Create user record on first login (JIT provisioning).
    Returns the User ORM object.
    """

async def require_student(user: User = Depends(get_current_user)) -> User:
    """Raises 403 if user.role != 'student'"""

async def require_institution_admin(user: User = Depends(get_current_user)) -> User:
    """Raises 403 if user.role != 'institution_admin'"""

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Raises 403 if user.role != 'admin'"""
```

**JIT (Just-In-Time) Provisioning:** When a user authenticates with a valid Cognito token but doesn't exist in our database yet, automatically create their `User` record. This keeps Cognito as the source of truth for auth while our DB tracks app-specific data.

### 4. services/auth_service.py — Auth Business Logic

```python
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, email: str, password: str, role: str) -> dict:
        """
        1. Create user in Cognito (boto3 sign_up + admin_confirm_sign_up for MVP)
        2. Create User record in our DB with cognito_sub
        3. If role == 'student': create empty StudentProfile
        4. If role == 'institution_admin': DON'T create Institution yet (that's a separate setup step)
        5. Return {user_id, email, role}
        """

    async def login(self, email: str, password: str) -> dict:
        """
        1. Call Cognito initiate_auth with USER_PASSWORD_AUTH
        2. Return {access_token, refresh_token, expires_in, token_type}
        """

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        1. Call Cognito initiate_auth with REFRESH_TOKEN_AUTH
        2. Return new {access_token, expires_in}
        """

    async def get_or_create_user(self, claims: CognitoClaims) -> User:
        """
        JIT provisioning: look up user by cognito_sub.
        If not found, create User record + StudentProfile if student.
        """
```

### 5. api/auth.py — Auth Routes

```
POST /api/v1/auth/signup
  Body: {email, password, role}
  Response: {user_id, email, role}
  Notes: role must be "student" or "institution_admin"

POST /api/v1/auth/login
  Body: {email, password}
  Response: {access_token, refresh_token, expires_in, token_type}

POST /api/v1/auth/refresh
  Body: {refresh_token}
  Response: {access_token, expires_in}

GET /api/v1/auth/me
  Headers: Authorization: Bearer <token>
  Response: {user_id, email, role, created_at}
  Notes: Verifies token, returns current user info
```

### 6. schemas/auth.py — Pydantic Schemas

```python
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["student", "institution_admin"]

class SignupResponse(BaseModel):
    user_id: UUID
    email: str
    role: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int
    token_type: str = "Bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    user_id: UUID
    email: str
    role: str
    created_at: datetime
```

### 7. Test Fixtures — Auth Mocks

Update `tests/conftest.py` to support testing without a real Cognito instance:

```python
@pytest.fixture
def mock_student_user():
    """Returns a User with role='student' for testing."""

@pytest.fixture
def mock_institution_user():
    """Returns a User with role='institution_admin' for testing."""

@pytest.fixture
def auth_headers_student(mock_student_user):
    """Returns {'Authorization': 'Bearer <fake_token>'} that bypasses Cognito verification."""

@pytest.fixture
def auth_headers_institution(mock_institution_user):
    """Returns auth headers for an institution admin."""
```

Override the `get_current_user` dependency in tests to return the mock user directly, skipping Cognito token verification.

### 8. Tests — test_auth.py

Write tests for:
- `POST /auth/signup` with valid student data → 201
- `POST /auth/signup` with valid institution_admin data → 201
- `POST /auth/signup` with invalid role → 422
- `POST /auth/signup` with weak password → 422
- `POST /auth/signup` with duplicate email → 409
- `POST /auth/login` with valid credentials → 200 with tokens
- `POST /auth/login` with wrong password → 401
- `GET /auth/me` with valid token → 200 with user info
- `GET /auth/me` without token → 401
- Role guards: student endpoint with institution token → 403
- Role guards: institution endpoint with student token → 403

**Note:** For tests that call Cognito (signup, login), mock the boto3 Cognito client. For tests that verify auth middleware, override the `get_current_user` dependency.

## Local Development Without AWS

For local development, support a `COGNITO_BYPASS=true` environment variable that:
1. Skips real Cognito verification in `verify_token()`
2. Accepts a special dev token format: `dev:<user_id>:<role>`
3. This lets developers test without AWS credentials

Add to `config.py`:
```python
cognito_bypass: bool = False  # Set to true for local dev without AWS
```

## Important Notes

- **Never store passwords** in our database — Cognito handles all password management
- **cognito_sub** is the link between Cognito and our DB — this is the stable user identifier
- Access tokens are short-lived (1 hour). The frontend uses refresh tokens to get new access tokens silently.
- The `custom:role` Cognito attribute is the source of truth for role. Our DB's `role` column is a cache for query convenience.
- All auth endpoints are public (no token required). All other endpoints require a valid token.
- Rate limit signup and login endpoints more aggressively (e.g., 10/minute) to prevent abuse
