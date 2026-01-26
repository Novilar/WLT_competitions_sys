import enum
from enum import Enum

class ApplicationType(str, enum.Enum):
    preliminary = "preliminary"
    final = "final"



class ApplicationStatus(str, Enum):
    draft = "draft"                    # представитель создает / редактирует
    submitted = "submitted"            # отправлено секретарю
    needs_correction = "needs_correction"  # возвращено на доработку
    prelim_verified = "prelim_verified"    # первичная проверка секретарем
    final_submitted = "final_submitted"    # подтверждение за 14 дней
    verified = "verified"              # окончательно принято
    rejected = "rejected"              # отклонено
