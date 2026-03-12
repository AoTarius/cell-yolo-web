from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_api, name='test_api'),

    # 登录相关接口
    path('login/', views.LoginView.as_view(), name='login'),
    path('update-user/', views.UpdateUserView.as_view(), name='update_user'),
    path('update-user-paths/', views.UpdateUserPathsView.as_view(), name='update_user_paths'),
    # 视频处理相关接口
    path('upload/', views.UploadVideoView.as_view(), name='upload_video'),
    path('process/', views.ProcessTaskView.as_view(), name='process_task'),
    path('status/<str:task_id>/', views.TaskStatusView.as_view(), name='task_status'),
    path('result/<str:task_id>/', views.TaskResultView.as_view(), name='task_result'),
    path('video/<str:task_id>/', views.AnnotatedVideoView.as_view(), name='annotated_video'),
    path('original-video/<str:task_id>/', views.OriginalVideoView.as_view(), name='original_video'),
    path('delete/<str:task_id>/', views.DeleteTaskView.as_view(), name='delete_task'),

    # 任务列表接口
    path('tasks/', views.TaskListView.as_view(), name='task_list'),

    # 模型列表接口
    path('models/', views.ModelListView.as_view(), name='model_list'),
    path('models/upload/', views.ModelUploadView.as_view(), name='upload_model'),
    path('models/delete/', views.DeleteModelView.as_view(), name='delete_model'),

    # 数据导出接口
    path('export/<str:task_id>/', views.ExportDataView.as_view(), name='export_data'),
]
