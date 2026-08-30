from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class CanonicalCodeDefinition:
    namespace: str
    code: str
    label: str
    active: bool = True
    rule_version: str | None = None
    metadata: Mapping | None = None

    @property
    def status(self) -> str:
        return "ACTIVE" if self.active else "INACTIVE"

@dataclass(frozen=True)
class CanonicalEducationalInputIdentity:
    grade: int
    ppct_position: int
    subject_code: str
    component_code: str | None = None
    lesson_plan_code: str | None = None
    equipment_code: str = "TB"

    @property
    def ppct_token(self):
        if self.ppct_position < 1: raise ValueError("ppct_position must be >= 1")
        return f"{self.ppct_position:03d}"
    @property
    def subject_business_id(self): return f"{self.grade}{self.subject_code}"
    @property
    def curriculum_business_id(self): return f"{self.grade}{self.component_code or self.subject_code}{self.ppct_token}"
    @property
    def lesson_plan_business_id(self):
        if not self.lesson_plan_code: raise ValueError("lesson_plan_code is required")
        return f"{self.grade}{self.lesson_plan_code}{self.ppct_token}"
    @property
    def lesson_plan_filename(self): return f"{self.lesson_plan_business_id}.docx"
    @property
    def equipment_group_business_id(self): return f"{self.grade}{self.equipment_code}{self.ppct_token}"
    def equipment_item_business_id(self, item_position):
        if item_position < 1: raise ValueError("item_position must be >= 1")
        return f"{self.equipment_group_business_id}-{item_position:02d}"

DEFAULT_CANONICAL_CODES: Mapping[str, CanonicalCodeDefinition] = {
 "subject.math": CanonicalCodeDefinition("subject","T","Toán"),
 "subject.english": CanonicalCodeDefinition("subject","A","Tiếng Anh"),
 "subject.arts": CanonicalCodeDefinition("subject","NT","Nghệ thuật"),
 "component.math.algebra": CanonicalCodeDefinition("component","TDS","Đại số"),
 "component.math.geometry": CanonicalCodeDefinition("component","THH","Hình học"),
 "component.math.statistics_probability": CanonicalCodeDefinition("component","TXS","Xác suất thống kê"),
 "component.arts.music": CanonicalCodeDefinition("component","NTN","Âm nhạc"),
 "lesson_plan.math": CanonicalCodeDefinition("lesson_plan","GT","Giáo án Toán"),
 "lesson_plan.math.algebra": CanonicalCodeDefinition("lesson_plan","GTDS","Giáo án Toán - Đại số"),
 "lesson_plan.math.geometry": CanonicalCodeDefinition("lesson_plan","GTHH","Giáo án Toán - Hình học"),
 "lesson_plan.math.statistics_probability": CanonicalCodeDefinition("lesson_plan","GXS","Giáo án Toán - Xác suất thống kê"),
 "lesson_plan.english": CanonicalCodeDefinition("lesson_plan","GTA","Giáo án Tiếng Anh"),
 "equipment": CanonicalCodeDefinition("equipment","TB","Thiết bị"),
}
def exact_lesson_plan_filename(identity): return identity.lesson_plan_filename
