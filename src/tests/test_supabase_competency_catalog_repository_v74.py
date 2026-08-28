from curriculum_v2.adapters.supabase_competency_catalog_repository import SupabaseCompetencyCatalogRepository
from curriculum_v2.models.competency_catalog import CompetencyIndicator

class Response:
    def __init__(self,data): self.data=data
class Query:
    def __init__(self,rows): self.rows=rows; self.payload=None
    def select(self,*a,**k): return self
    def order(self,*a,**k): return self
    def eq(self,*a,**k): return self
    def upsert(self,payload,**k): self.payload=payload; self.rows=[payload]; return self
    def update(self,payload): self.payload=payload; return self
    def execute(self): return Response(self.rows)
class Client:
    def __init__(self,rows): self.rows=rows
    def table(self,name): return Query(self.rows.get(name,[]))

def test_repository_reads_frameworks_and_indicators():
    client=Client({
        "competency_frameworks":[{"framework_id":"framework-eng","canonical_code":"ENG","framework_name":"English","framework_type":"SUBJECT_SPECIFIC","subject_id":"subject-foreign-language-1","version_label":"1.2","provenance_status":"REVIEWED","status":"ACTIVE","metadata":{}}],
        "competency_indicators":[{"indicator_id":"i1","framework_id":"framework-eng","component_id":None,"canonical_code":"ENG.COM.L.I01","source_code":"L","indicator_name":"Listening","indicator_text":"Nghe","observable_flag":True,"assessable_flag":True,"version_label":"1.2","provenance_status":"REVIEWED","status":"ACTIVE","metadata":{}}]
    })
    repo=SupabaseCompetencyCatalogRepository(client=client)
    assert repo.list_frameworks()[0].canonical_code=="ENG"
    assert repo.list_indicators(framework_id="framework-eng")[0].canonical_code=="ENG.COM.L.I01"

def test_repository_rejects_empty_update():
    repo=SupabaseCompetencyCatalogRepository(client=Client({}))
    try:
        repo.update_indicator_fields(indicator_id="i1",values={"not_allowed":1})
    except ValueError:
        return
    raise AssertionError("expected ValueError")
