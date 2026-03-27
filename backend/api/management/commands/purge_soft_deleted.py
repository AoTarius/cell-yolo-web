"""
清理软删除数据的管理命令
用法: python manage.py purge_soft_deleted [--days 30] [--dry-run] [--force]
选项:
--days: 保留天数，默认为30天，删除超过这个时间的软删除数据，考虑UTC时间
--dry-run: 只显示将要删除的记录，不实际删除
--force: 强制删除所有软删除记录，不考虑时间限制
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = '清理超过指定天数的软删除数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='保留天数，默认为30天'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要删除的记录，不实际删除'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制删除所有软删除记录，不考虑时间限制'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        force = options['force']
        
        if force:
            # 强制删除模式：删除所有软删除记录
            self.stdout.write(self.style.WARNING('强制模式：将删除所有软删除记录，不考虑时间限制'))
        else:
            # 正常模式：按时间删除
            cutoff_date = timezone.now() - timedelta(days=days)
            self.stdout.write(f'开始清理 {days} 天前的软删除数据...')
            self.stdout.write(f'截止时间: {cutoff_date}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 模式：只显示，不删除'))
        
        # 导入模型（需要在Django环境初始化后导入）
        from api.models import User, Video, ModelFile, Task, Cell, TaskStatus
        from django.db import connection
        
        total_deleted = 0
        
        # 清理每个表的软删除数据
        models_to_clean = [
            ('User', User),
            ('Video', Video),
            ('ModelFile', ModelFile),
            ('Task', Task),
            ('Cell', Cell),
            ('TaskStatus', TaskStatus),
        ]
        
        # 实际删除时禁用外键检查，避免外键约束错误
        if not dry_run:
            with connection.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        try:
            for model_name, model_class in models_to_clean:
                try:
                    # 使用 all_objects 包含已删除的记录
                    if force:
                        # 强制模式：删除所有软删除记录
                        deleted_records = model_class.all_objects.filter(is_deleted=True)
                    else:
                        # 正常模式：按时间删除
                        deleted_records = model_class.all_objects.filter(
                            is_deleted=True,
                            deleted_at__lt=cutoff_date
                        )
                    
                    count = deleted_records.count()
                    
                    if count > 0:
                        self.stdout.write(f'{model_name}: 找到 {count} 条记录')
                        
                        if not dry_run:
                            # 实际删除
                            deleted_records.delete()
                            self.stdout.write(
                                self.style.SUCCESS(f'{model_name}: 已删除 {count} 条记录')
                            )
                        else:
                            # 显示示例记录
                            sample = deleted_records.first()
                            if sample:
                                self.stdout.write(f'  示例记录 ID: {sample.id}, 删除时间: {sample.deleted_at}')
                        
                        total_deleted += count
                    else:
                        self.stdout.write(f'{model_name}: 无需清理')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'{model_name}: 清理失败 - {str(e)}')
                    )
        finally:
            # 重新启用外键检查
            if not dry_run:
                with connection.cursor() as cursor:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        # 总结
        action_text = "将删除" if dry_run else "已删除"
        self.stdout.write(self.style.SUCCESS(
            f'\n清理完成！总共 {action_text} {total_deleted} 条记录'
        ))
