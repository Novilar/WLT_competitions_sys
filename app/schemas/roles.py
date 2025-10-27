from enum import Enum


class GlobalRole(str, Enum):
    super_admin = "super_admin"
    athlete = "athlete"


class CompetitionRoleEnum(str, Enum):
    organizer = "organizer"
    commission_member = "commission_member"
    secretary = "secretary"
    marshal = "marshal"
    judge = "judge"
    jury_member = "jury_member"
    jury_head = "jury_head"
    athlete = "athlete"
