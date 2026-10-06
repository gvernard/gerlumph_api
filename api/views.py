from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions, status
from rest_framework.parsers import  MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer

from gerlumph_maps.models import MagMaps
from gerlumph_downloads.models import Downloads
from gerlumph_users.models import Users

from .serializers import MapIdsSerializer


class FetchMapLinks(APIView):
    authentication_classes = [authentication.SessionAuthentication,authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self,request):
        serializer = MapIdsSerializer(data=request.data)
        if serializer.is_valid():
            maps = serializer.validated_data["ids"]

            links = []
            for mappa in maps:
                links.append( mappa.get_file_url("map.bin") )
                links.append( mappa.get_file_url("mapmeta.dat") )


            new_download = Downloads.objects.create(owner=request.user)
            new_download.maps.set(maps)            
                
            return Response({"links": links}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
 
