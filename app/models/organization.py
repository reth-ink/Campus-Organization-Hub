class Organization:
    def __init__(self, OrgID, OrgName, OrgDescription=None, Description=None, **kwargs):
        self.OrgID = OrgID
        self.OrgName = OrgName
        # Accept either OrgDescription or Description column names from DB/CSV
        self.OrgDescription = OrgDescription if OrgDescription is not None else Description

        # Attach any additional fields silently to avoid unexpected kwarg errors
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "OrgID": self.OrgID,
            "OrgName": self.OrgName,
            "OrgDescription": self.OrgDescription,
            # optional UI fields
            "contact_email": getattr(self, 'contact_email', None),
            "created_at": getattr(self, 'created_at', None)
        }