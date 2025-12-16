class Event:
    def __init__(self, EventID, OrgID, CreatedBy, EventName=None, EventDescription=None, Description=None, EventDate=None, Location=None, **kwargs):
        self.EventID = EventID
        self.OrgID = OrgID
        self.CreatedBy = CreatedBy
        # Accept either EventDescription or Description column names
        self.EventName = EventName
        self.EventDescription = EventDescription if EventDescription is not None else Description
        self.EventDate = EventDate
        self.Location = Location

        # Attach additional fields (created_at, updated_at, etc.) if present
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "EventID": self.EventID,
            "OrgID": self.OrgID,
            "CreatedBy": self.CreatedBy,
            "EventName": self.EventName,
            "EventDescription": self.EventDescription,
            "EventDate": self.EventDate,
            "Location": self.Location
        }
    