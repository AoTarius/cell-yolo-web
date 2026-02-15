from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_api, name='test_api'),

    # 视频处理相关接口
    path('upload/', views.UploadVideoView.as_view(), name='upload_video'),
    path('process/', views.ProcessTaskView.as_view(), name='process_task'),
    path('status/<str:task_id>/', views.TaskStatusView.as_view(), name='task_status'),
    path('result/<str:task_id>/', views.TaskResultView.as_view(), name='task_result'),
    path('video/<str:task_id>/', views.AnnotatedVideoView.as_view(), name='annotated_video'),
    
    # 任务列表接口
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
]
