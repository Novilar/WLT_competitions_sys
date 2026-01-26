from app.models import ApplicationStatus

def is_transition_allowed(
    from_status: ApplicationStatus,
    to_status: ApplicationStatus,
) -> bool:
    return to_status in STATUS_TRANSITIONS.get(from_status, set())




STATUS_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.draft: {
        ApplicationStatus.submitted,
    },
    ApplicationStatus.needs_correction: {
        ApplicationStatus.submitted,
    },
    ApplicationStatus.submitted: {
        ApplicationStatus.prelim_verified,
        ApplicationStatus.needs_correction,
    },
    ApplicationStatus.prelim_verified: {
        ApplicationStatus.final_submitted,
    },
    ApplicationStatus.final_submitted: {
        ApplicationStatus.verified,
        ApplicationStatus.rejected,
    },
}
