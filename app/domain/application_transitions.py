from app.models import ApplicationStatus

ROLE_TRANSITIONS = {
    ApplicationStatus.draft: {
        "athlete": [ApplicationStatus.submitted],
    },
    ApplicationStatus.submitted: {
        "secretary": [
            ApplicationStatus.prelim_verified,
            ApplicationStatus.needs_correction,
        ],
    },
    ApplicationStatus.needs_correction: {
        "athlete": [ApplicationStatus.submitted],
    },
    ApplicationStatus.final_submitted: {
        "secretary": [
            ApplicationStatus.verified,
            ApplicationStatus.rejected,
        ],
    },
}