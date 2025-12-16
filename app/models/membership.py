class Membership:
    def __init__(self, MembershipID, UserID, OrgID, Status=None, DateApplied=None, DateApproved=None, created_at=None, updated_at=None, **kwargs):
        self.MembershipID = MembershipID
        self.UserID = UserID
        self.OrgID = OrgID
        self.Status = Status
        self.DateApplied = DateApplied
        self.DateApproved = DateApproved

        # attach optional audit timestamps and any additional fields
        self.created_at = created_at
        self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "MembershipID": self.MembershipID,
            "UserID": self.UserID,
            "OrgID": self.OrgID,
            "Status": self.Status,
            "DateApplied": self.DateApplied,
            "DateApproved": self.DateApproved
        }