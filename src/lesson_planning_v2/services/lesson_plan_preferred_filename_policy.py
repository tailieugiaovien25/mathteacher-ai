from __future__ import annotations
from dataclasses import dataclass
import re

class PreferredLessonPlanFilenameError(ValueError):
    pass

@dataclass(frozen=True, slots=True)
class PreferredLessonPlanFilename:
    basename: str
    filename: str

def _code(value):
    code=str(value or "").strip().upper()
    if not code or not re.fullmatch(r"[A-Z0-9]+",code):
        raise PreferredLessonPlanFilenameError("PREFERRED_FILENAME_CODE_REQUIRED")
    return code

def _positive(value,error):
    try: number=int(value)
    except (TypeError,ValueError): raise PreferredLessonPlanFilenameError(error)
    if number < 1: raise PreferredLessonPlanFilenameError(error)
    return number

def preferred_filename(*,code,grade,week_number=None,lesson_number=None,curriculum_period=None):
    code=_code(code); grade=_positive(grade,"PREFERRED_FILENAME_GRADE_REQUIRED")
    if week_number is not None:
        base=f"KHBD.{code}{grade}.TUAN{_positive(week_number,'PREFERRED_FILENAME_WEEK_REQUIRED'):02d}"
    elif lesson_number is not None:
        base=f"KHBD.{code}{grade}.BAI{_positive(lesson_number,'PREFERRED_FILENAME_LESSON_REQUIRED'):02d}"
    elif curriculum_period is not None:
        base=f"KHBD.{code}{grade}.{_positive(curriculum_period,'PREFERRED_FILENAME_PERIOD_REQUIRED'):03d}"
    else:
        raise PreferredLessonPlanFilenameError("PREFERRED_FILENAME_GROUP_POSITION_REQUIRED")
    return PreferredLessonPlanFilename(base,base+".docx")

def preferred_code_from_group(group):
    # Runtime/configured refs only; no hard-coded subject map.
    return str(getattr(group,"component_ref","") or getattr(group,"subject_ref","") or "").strip()
