"""
清理软删除数据的管理命令
用法: python manage.py purge_soft_deleted [--days 30] [--dry-run]
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

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # 计算截止时间
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f'开始清理 {days} 天前的软删除数据...')
        self.stdout.write(f'截止时间: {cutoff_date}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 模式：只显示，不删除'))
        
        # 导入模型（需要在Django环境初始化后导入）
        from api.models import User, Video, ModelFile, Task, Cell, TaskStatus
        
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
        
        for model_name, model_class in models_to_clean:
            try:
                # 使用 all_objects 包含已删除的记录
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
        
        # 总结
        action_text = "将删除" if dry_run else "已删除"
        self.stdout.write(self.style.SUCCESS(
            f'\n清理完成！总共 {action_text} {total_deleted} 条记录'
        ))
