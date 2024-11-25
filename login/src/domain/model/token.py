class Token:
    access_token: str
    token_type: str

    def __init__(self, access_token: str, token_type: str):
        super().__init__()
        self.access_token = access_token
        self.token_type = token_type
