import os
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import BackupLog
from .serializers import BackupLogSerializer
from utils.permissions import IsAdmin

class BackupViewSet(viewsets.ModelViewSet):
    queryset = BackupLog.objects.all()
    serializer_class = BackupLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def perform_destroy(self, instance):
        """Xóa file vật lý khi xóa bản ghi"""
        try:
            if instance.backup_path:
                # Chuyển đường dẫn URL (/media/...) thành đường dẫn hệ thống
                # Loại bỏ dấu / ở đầu để join đúng với BASE_DIR
                relative_path = instance.backup_path.lstrip('/')
                file_path = os.path.join(settings.BASE_DIR, relative_path)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"--- [BACKUP] Đã xóa file: {file_path}")
                else:
                    print(f"--- [BACKUP] Không tìm thấy file để xóa: {file_path}")
        except Exception as e:
            print(f"--- [BACKUP ERROR] Lỗi khi xóa file: {e}")
            
        # Xóa bản ghi trong DB
        instance.delete()
    
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """Tạo bản sao lưu dữ liệu THẬT (dạng JSON)"""
        try:
            backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            filename = f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(backup_dir, filename)
            
            print(f"--- [BACKUP] Đang tạo file: {filepath} ---")
            with open(filepath, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata', 
                    exclude=['contenttypes', 'auth.permission', 'sessions', 'admin.logentry'],
                    indent=2, 
                    stdout=f
                )
            
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            
            backup = BackupLog.objects.create(
                backup_type='manual',
                backup_path=f'/media/backups/{filename}',
                file_name=filename,
                file_size_mb=round(file_size, 4),
                status='success',
                performed_by=request.user,
                tables_backed_up=['all']
            )
            
            return Response(BackupLogSerializer(backup).data)

        except Exception as e:
            print(f"--- [BACKUP ERROR] {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Phục hồi dữ liệu"""
        backup = self.get_object()
        file_path = os.path.join(settings.BASE_DIR, backup.backup_path.lstrip('/'))
        
        if not os.path.exists(file_path):
            return Response({'error': 'Không tìm thấy file backup.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            print(f"--- [RESTORE] Đang nạp dữ liệu từ: {file_path} ---")
            call_command('loaddata', file_path)
            return Response({'message': 'Phục hồi dữ liệu thành công!'})
        except Exception as e:
            return Response({'error': f'Lỗi phục hồi: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)