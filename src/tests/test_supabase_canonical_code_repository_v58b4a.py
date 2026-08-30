from pathlib import Path
from portal_v2.context.canonical_code_catalog import CanonicalCodeDefinition
from portal_v2.context.supabase_canonical_code_repository import SupabaseCanonicalCodeRepository

ROOT=Path(__file__).resolve().parents[2]
SQL=(ROOT/"supabase/migrations/202608290002_canonical_code_registry_v58b2.sql").read_text(encoding="utf-8").lower()

class Response:
 def __init__(self,data): self.data=data

class Query:
 def __init__(self,rows): self.rows=rows; self.filters=[]
 def select(self,*a,**k): return self
 def eq(self,k,v): self.filters.append((k,v)); return self
 def order(self,*a,**k): return self
 def limit(self,*a,**k): return self
 def upsert(self,payload,**kwargs):
  self.rows[:] = [r for r in self.rows if not (r["namespace"]==payload["namespace"] and r["code"]==payload["code"])]
  self.rows.append(dict(payload)); return self
 def execute(self):
  rows=[r for r in self.rows if all(str(r.get(k))==str(v) for k,v in self.filters)]
  return Response(rows)

class Client:
 def __init__(self,rows): self.rows=rows
 def table(self,name):
  assert name=="canonical_code_registry"
  return Query(self.rows)

def test_supabase_repository_reads_and_writes_registry():
 rows=[{"namespace":"subject","code":"T","label":"Toán","status":"ACTIVE"}]
 repo=SupabaseCanonicalCodeRepository(Client(rows))
 assert repo.get_code(namespace="subject",code="T").label=="Toán"
 repo.save_code(CanonicalCodeDefinition("subject","A","Tiếng Anh",True))
 assert repo.get_code(namespace="subject",code="A").label=="Tiếng Anh"

def test_rls_registry_is_admin_write_but_authenticated_read():
 assert "canonical_code_registry_authenticated_read" in SQL
 assert "canonical_code_registry_admin_write" in SQL
 assert "from public.portal_roles pr" in SQL
 assert "pr.user_id = (select auth.uid())" in SQL
 assert "pr.role = 'admin'" in SQL
 assert "public.is_portal_admin()" not in SQL

def test_teacher_input_is_owner_scoped():
 assert "canonical_teacher_input_owner_read" in SQL
 assert "owner_user_id = (select auth.uid())" in SQL

def test_rls_enabled_on_all_v58b2_tables():
 for table in (
  "canonical_code_registry","canonical_code_mappings",
  "canonical_code_generation_rules","canonical_teacher_educational_inputs"
 ):
  assert f"alter table public.{table} enable row level security" in SQL
