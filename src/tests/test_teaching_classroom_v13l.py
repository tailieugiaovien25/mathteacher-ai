import sys
sys.path.insert(0, '/mnt/data/v13k_work/src')
from ai_kernel.contracts import AIActionClass
from ai_kernel.teaching_assistant import TeachingAssistantController, TeachingAssistantAction, default_teaching_personas, default_teaching_policy, TeachingAssistantMode
from ai_kernel.teaching_classroom import ClassroomPhase, LessonActivityContext, TeachingClassroomOrchestrator
from ai_kernel.teaching_classroom_executor import StreamlitClassroomRuntime, TeachingClassroomActionExecutor, ClassroomExecutionStatus

p=default_teaching_personas()[0]
ctl=TeachingAssistantController(persona=p, policy=default_teaching_policy(p.persona_id))
s={'lesson_slide_ids':['s1','s2'], 'lesson_integrated_stages':{'stage1':b'<html></html>'}}
r=StreamlitClassroomRuntime(s)
e=TeachingClassroomActionExecutor(controller=ctl,runtime=r)
o=TeachingClassroomOrchestrator()
ctx=LessonActivityContext('l','a2','Hoạt động 2',ClassroomPhase.NEW_KNOWLEDGE,duration_seconds=10,selected_slide_id='s2',question='Q',allowed_tools=('classroom.surface.clear_overlays','classroom.slide.open','classroom.timer.start'))
# Seed old overlays
r.execute(TeachingAssistantAction('stage','classroom.stage.show','stage',AIActionClass.MUTATING,{'content_id':'stage1'},True)) if False else None
s['ta_classroom_runtime_state_v13k']={'stage':{'content_id':'stage1'},'quiz':{'question':'old'},'whiteboard':{'content':'old'}}
plan=o.build_plan(context=ctx,mode=TeachingAssistantMode.MC,include_slide=True,include_timer=True,clear_overlays=True)
assert plan.actions[0].tool_id=='classroom.surface.clear_overlays'
for a in plan.actions:
    rr=e.execute(a,teacher_confirmed=True)
    assert rr.status is ClassroomExecutionStatus.EXECUTED, rr
state=r.read_status()
assert 'stage' not in state and 'quiz' not in state and 'whiteboard' not in state
assert state['selected_slide_id']=='s2'
print('V13L transition cleanup PASS')
