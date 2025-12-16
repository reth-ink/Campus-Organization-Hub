class User:
    def __init__(self, UserID, FirstName, LastName, Email, PasswordHash=None, **kwargs):
        # Core visible fields
        self.UserID = UserID
        self.FirstName = FirstName
        self.LastName = LastName
        self.Email = Email

        # Internal / optional fields (keep but don't expose in to_dict)
        self.PasswordHash = PasswordHash

        # Accept and ignore any additional fields coming from DB rows
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        # Do NOT include PasswordHash when serializing for responses
        return {
            "UserID": self.UserID,
            "FirstName": self.FirstName,
            "LastName": self.LastName,
            "Email": self.Email
        }