from .org_service import OrgService
from .membership_service import MembershipService
from .officer_role_service import OfficerRoleService
from .event_service import EventService
from .announcement_service import AnnouncementService
from .user_service import UserService

class ImportService:

    @staticmethod
    def import_all():
        # Import in the correct order to satisfy foreign keys
        UserService.import_from_csv()
        OrgService.import_from_csv()
        MembershipService.import_from_csv()
        OfficerRoleService.import_from_csv()
        EventService.import_from_csv()
        AnnouncementService.import_from_csv()
