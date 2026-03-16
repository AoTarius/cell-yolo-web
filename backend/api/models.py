"""
Django ORM 模型定义
映射 cell_tracking 数据库的5个核心表
"""

from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """软删除管理器，默认只查询未删除的记录"""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """所有记录管理器，包括已删除的记录"""

    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):
    """基础模型，包含软删除字段"""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')

    objects = SoftDeleteManager()  # 默认管理器，只查询未删除的记录
    all_objects = AllObjectsManager()  # 所有记录管理器，包括已删除的

    class Meta:
        abstract = True

    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """恢复已删除的记录"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class User(BaseModel):
    """用户表"""

    username = models.CharField(max_length=100, unique=True, verbose_name='用户名')
    email = models.CharField(max_length=255, null=True, blank=True, verbose_name='邮箱')
    password_hash = models.CharField(max_length=255, verbose_name='密码哈希')
    dark_mode = models.BooleanField(default=True, verbose_name='深色模式')
    model_base_path = models.CharField(max_length=500, verbose_name='模型基础路径')
    output_base_path = models.CharField(max_length=500, verbose_name='输出基础路径')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return self.username


class Video(BaseModel):
    """视频表"""

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column='user_id', verbose_name='所属用户')
    video_name = models.CharField(max_length=255, verbose_name='视频名称')
    video_path = models.CharField(max_length=255, verbose_name='视频路径')
    total_frames = models.IntegerField(null=True, blank=True, verbose_name='总帧数')
    video_duration = models.FloatField(null=True, blank=True, verbose_name='视频时长（秒）')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='文件大小（字节）')

    class Meta:
        db_table = 'videos'
        verbose_name = '视频'
        verbose_name_plural = '视频'
        unique_together = ['user', 'video_name']  # 同一用户内视频名称唯一
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.user.username}/{self.video_name}"


class ModelFile(BaseModel):
    """模型表（避免与 models 模块冲突）"""

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column='user_id', verbose_name='所属用户')
    model_name = models.CharField(max_length=100, verbose_name='模型名称')
    model_path = models.CharField(max_length=255, verbose_name='模型路径')

    class Meta:
        db_table = 'models'
        verbose_name = '模型'
        verbose_name_plural = '模型'
        unique_together = ['user', 'model_name']  # 同一用户内模型名称唯一
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.user.username}/{self.model_name}"


class Task(BaseModel):
    """任务表"""

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column='user_id', verbose_name='所属用户')
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, db_column='video_id', verbose_name='视频')
    model = models.ForeignKey(ModelFile, on_delete=models.DO_NOTHING, db_column='model_id', verbose_name='模型')
    task_id = models.CharField(max_length=36, unique=True, verbose_name='任务ID')
    task_name = models.CharField(max_length=255, verbose_name='任务名称')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    total_frames = models.IntegerField(default=0, verbose_name='总帧数')
    conf = models.FloatField(default=0.3, verbose_name='置信度阈值')
    imgsz = models.IntegerField(default=1024, verbose_name='图像尺寸')
    fps = models.IntegerField(default=10, verbose_name='帧率')
    annotated_video_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='标注视频名称')
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')

    class Meta:
        db_table = 'tasks'
        verbose_name = '任务'
        verbose_name_plural = '任务'
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['user']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['video']),
            models.Index(fields=['model']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'status', 'is_deleted']),
        ]

    def __str__(self):
        return f"{self.task_name} ({self.task_id})"


class Cell(BaseModel):
    """细胞表"""

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING, db_column='task_id', verbose_name='所属任务')
    frame = models.IntegerField(verbose_name='帧号')
    track_id = models.IntegerField(verbose_name='轨迹ID')
    bb_left = models.FloatField(verbose_name='边界框左上角X')
    bb_top = models.FloatField(verbose_name='边界框左上角Y')
    bb_width = models.FloatField(verbose_name='边界框宽度')
    bb_height = models.FloatField(verbose_name='边界框高度')
    conf = models.FloatField(verbose_name='置信度')
    class_id = models.IntegerField(default=0, verbose_name='类别')
    visibility = models.FloatField(null=True, blank=True, verbose_name='可见性')

    class Meta:
        db_table = 'cells'
        verbose_name = '细胞'
        verbose_name_plural = '细胞'
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['task', 'frame', 'track_id']),
            models.Index(fields=['task', 'track_id']),
            models.Index(fields=['task', 'frame']),
            models.Index(fields=['task', 'is_deleted']),
        ]

    def __str__(self):
        return f"Task {self.task.task_id} - Frame {self.frame} - Track {self.track_id}"

class TaskStatus(BaseModel):
    """任务实时状态表"""

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    task = models.OneToOneField(Task, on_delete=models.CASCADE, db_column='task_id', to_field='task_id', verbose_name='关联任务')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    progress = models.IntegerField(default=0, verbose_name='进度（0-100）')
    stage = models.CharField(max_length=50, null=True, blank=True, verbose_name='当前阶段')
    current_frame = models.IntegerField(default=0, verbose_name='当前处理帧数')
    total_frames = models.IntegerField(default=0, verbose_name='总帧数')
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')
    estimated_remaining_time = models.IntegerField(null=True, blank=True, verbose_name='预计剩余时间（秒）')

    class Meta:
        db_table = 'task_status'
        verbose_name = '任务状态'
        verbose_name_plural = '任务状态'
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['task', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Task {self.task.task_id} - {self.status} - Frame {self.current_frame}/{self.total_frames}"