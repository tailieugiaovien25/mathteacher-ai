from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import re

@dataclass(frozen=True, slots=True)
class LocalLessonPlanMatch:
    path: Path
    match_reason: str

def _identity(value):
    text=Path(str(value or "")).name.casefold().strip()
    text=re.sub(r"\.docx$","",text)
    text=re.sub(r"[\s_-]+",".",text)
    text=re.sub(r"\.+",".",text).strip(".")
    text=re.sub(r"(?<=tuan)(\d{1,2})$",lambda m:f"{int(m.group(1)):02d}",text)
    text=re.sub(r"(?<=bai)(\d{1,2})$",lambda m:f"{int(m.group(1)):02d}",text)
    return text

def default_search_roots():
    home=Path.home()
    return tuple(p for p in (home/"Documents",home/"Downloads",home/"Desktop") if p.is_dir())

def configured_search_roots():
    raw=str(os.environ.get("MATHTEACHER_LESSON_PLAN_SEARCH_DIRS","") or "").strip()
    if not raw: return default_search_roots()
    result=[]
    for value in raw.split(os.pathsep):
        p=Path(value.strip()).expanduser()
        if value.strip() and p.is_dir(): result.append(p)
    return tuple(result)

def find_local_lesson_plans(*,preferred_file_name="",legacy_file_name="",aliases=(),roots=None):
    preferred=_identity(preferred_file_name)
    legacy=_identity(legacy_file_name)
    alias_ids={_identity(x) for x in aliases if str(x or "").strip()}
    found=[]; seen=set()
    for root in tuple(roots) if roots is not None else configured_search_roots():
        try:
            for path in Path(root).rglob("*.docx"):
                try:
                    ident=_identity(path.name)
                    if preferred and ident==preferred: reason="LOCAL_PREFERRED_FILENAME"
                    elif legacy and ident==legacy: reason="LOCAL_LEGACY_FILENAME"
                    elif ident and ident in alias_ids: reason="LOCAL_ALIAS_FILENAME"
                    else: continue
                    key=str(path.resolve()).casefold()
                    if key not in seen:
                        seen.add(key); found.append(LocalLessonPlanMatch(path,reason))
                except (OSError,PermissionError): continue
        except (OSError,PermissionError): continue
    order={"LOCAL_PREFERRED_FILENAME":0,"LOCAL_LEGACY_FILENAME":1,"LOCAL_ALIAS_FILENAME":2}
    found.sort(key=lambda x:(order.get(x.match_reason,99),str(x.path).casefold()))
    return tuple(found)

def read_local_lesson_plan(match):
    content=match.path.read_bytes()
    if not content: raise ValueError("LOCAL_LESSON_PLAN_EMPTY")
    return content
