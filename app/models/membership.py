class Membership:
    def __init__(self, MembershipID, UserID, OrgID, Status, DateApplied, DateApproved):
        self.MembershipID = MembershipID
        self.UserID = UserID
        self.OrgID = OrgID
        self.Status = Status
        self.DateApplied = DateApplied
        self.DateApproved = DateApproved
    
    def to_dict(self):
        return {
            "MembershipID": self.MembershipID,
            "UserID": self.UserID,
            "OrgID": self.OrgID,
            "Status": self.Status,
            "DateApplied": self.DateApplied,
            "DateApproved": self.DateApproved
        }