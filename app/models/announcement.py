class Announcement:
    def __init__(self, AnnouncementID, OrgID, CreatedBy, Title, Content, DatePosted=None, created_at=None, updated_at=None, **kwargs):
        self.AnnouncementID = AnnouncementID
        self.OrgID = OrgID
        self.CreatedBy = CreatedBy
        self.Title = Title
        self.Content = Content
        self.DatePosted = DatePosted

        # attach optional audit timestamps and any additional fields
        self.created_at = created_at
        self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "AnnouncementID": self.AnnouncementID,
            "OrgID": self.OrgID,
            "CreatedBy": self.CreatedBy,
            "Title": self.Title,
            "Content": self.Content,
            "DatePosted": self.DatePosted,
            # UI helpers — may be None if not provided by services
            "flair": getattr(self, 'flair', None),
            "link": getattr(self, 'link', None)
        }