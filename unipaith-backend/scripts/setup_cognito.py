"""
Run once to create Cognito User Pool and App Client.
Outputs the pool_id and client_id to add to .env

Usage: python -m scripts.setup_cognito
"""
import boto3

from unipaith.config import settings


def main() -> None:
    client = boto3.client(
        "cognito-idp",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    pool_resp = client.create_user_pool(
        PoolName="unipaith-users",
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": True,
                "RequireLowercase": True,
                "RequireNumbers": True,
                "RequireSymbols": False,
            }
        },
        AutoVerifiedAttributes=["email"],
        UsernameAttributes=["email"],
        Schema=[
            {
                "Name": "email",
                "AttributeDataType": "String",
                "Required": True,
                "Mutable": True,
            },
            {
                "Name": "role",
                "AttributeDataType": "String",
                "Required": False,
                "Mutable": True,
                "StringAttributeConstraints": {"MinLength": "1", "MaxLength": "30"},
            },
        ],
    )
    pool_id = pool_resp["UserPool"]["Id"]

    client_resp = client.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName="unipaith-api",
        GenerateSecret=False,
        ExplicitAuthFlows=[
            "ALLOW_USER_PASSWORD_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH",
        ],
        AccessTokenValidity=1,  # 1 hour
        RefreshTokenValidity=30,  # 30 days
        TokenValidityUnits={
            "AccessToken": "hours",
            "RefreshToken": "days",
        },
    )
    client_id = client_resp["UserPoolClient"]["ClientId"]

    print(f"\nCOGNITO_USER_POOL_ID={pool_id}")
    print(f"COGNITO_APP_CLIENT_ID={client_id}")
    print("\nAdd these to your .env file.")


if __name__ == "__main__":
    main()
