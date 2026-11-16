class FakeEmailSender:
    is_configured = True

    def __init__(self) -> None:
        self.verification_tokens: dict[str, str] = {}
        self.password_reset_tokens: dict[str, str] = {}

    def send_verification(self, email: str, token: str) -> None:
        self.verification_tokens[email] = token

    def send_password_reset(self, email: str, token: str) -> None:
        self.password_reset_tokens[email] = token
