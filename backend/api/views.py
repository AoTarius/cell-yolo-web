from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def test_api(request):
    return Response({
        'message': 'Django + Vue 前后端分离项目已启动！',
        'status': 'success'
    }, status=status.HTTP_200_OK)
