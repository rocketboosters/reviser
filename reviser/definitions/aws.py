import typing

import boto3
from botocore.client import BaseClient
from botocore.credentials import Credentials


class AwsConnection:
    """Boto3 Session wrapper that facilitates broader session management."""

    def __init__(self, session: boto3.Session = None):
        """..."""
        self._session = session or boto3.Session()
        self._aws_account = self.client("sts").get_caller_identity()
        self._aws_account_aliases = self.client("iam").list_account_aliases()

    @property
    def session(self) -> boto3.Session:
        """Returns the session object associated with this connection."""
        return self._session

    @property
    def user_id(self) -> str:
        """Returns the fully-qualified user ID for the associated session."""
        return self._aws_account.get("UserId")

    @property
    def user_arn(self) -> str:
        """Returns the ARN of the user associated with this session."""
        return self._aws_account.get("Arn")

    @property
    def user_slug(self) -> str:
        """
        Display slug from the user ARN containing account ID and user
        name or assumed role for use in shell prompt.
        """
        if "iam::" in self.user_arn:
            return self.user_arn.split("iam::")[-1]
        return self.user_arn.split("sts::")[-1].rsplit("/", 1)[0]

    @property
    def aws_account_id(self) -> str:
        """Returns the AWS account ID for the associated session."""
        return self._aws_account.get("Account")

    @property
    def aws_account_alias(self) -> typing.Optional[str]:
        """
        Returns the AWS account alias for the account associated with
        the session.
        """
        aliases = self._aws_account_aliases.get("AccountAliases")
        if aliases:
            return aliases[0]
        return None

    def get_credentials(self) -> Credentials:
        """Returns the credentials associated with the session."""
        return self.session.get_credentials()

    def client(self, *args, **kwargs) -> BaseClient:
        """Creates a new client of the specified type."""
        return self._session.client(*args, **kwargs)
