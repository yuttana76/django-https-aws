from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response


from .models import mit_master_value
from .serializers import *

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def getconsent(request):
    print("*** getconsent with user:", request.user)
    print("*** data:", request.data)

    if 'compCode' in request.data:
        compCode = request.data['compCode']
        response = mit_cmp_consentmas.objects.filter(
            compCode__iexact=compCode, consStatus="A").order_by("seq")
        serializer = CmpConsentMasSerializerShort(response, many=True)
        response = {'code': '000', 'message': 'Succesful',
                    'result': serializer.data}
        return Response(response, status=status.HTTP_200_OK)
    else:
        response = {'message': 'You need to provide response data'}
    return Response(response, status=status.HTTP_400_BAD_REQUEST)
