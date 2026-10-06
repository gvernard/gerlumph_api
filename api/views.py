from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions, status
from rest_framework.parsers import  MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer
from django.db.models.functions import Abs, Power, Sqrt
from django.db.models import Value, F, Q, FloatField

from gerlumph_maps.models import MagMaps
from gerlumph_downloads.models import Downloads
from gerlumph_users.models import Users

from .serializers import MapIdsSerializer, QuerySingleMapSerializer



class QuerySingleMap(APIView):
    authentication_classes = [authentication.SessionAuthentication,authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self,request):
        serializer = QuerySingleMapSerializer(data=request.data)
        if serializer.is_valid():
            k0 = serializer.validated_data["k"]
            g0 = serializer.validated_data["g"]
            s0 = serializer.validated_data["s"]
            dkg_tol = serializer.validated_data["dkg_tol"]
            ds_tol = serializer.validated_data["ds_tol"]

            match_qset = MagMaps.objects.annotate(
                dkg=Sqrt(
                    Power(F('kappa') - k0, 2) + 
                    Power(F('gamma') - g0, 2),
                    output_field=FloatField()
                ),
            ).annotate(
                ds=Abs(F('s')-s0,output_field=FloatField()),
            ).filter(
                dkg__lt=dkg_tol
            ).order_by(
                'dkg','ds'
            )

            if match_qset:
                map_obj = match_qset.first()
                mymap = {}
                mymap["id"] = map_obj.id
                mymap["k"] = map_obj.kappa
                mymap["g"] = map_obj.gamma
                mymap["s"] = map_obj.s
                return Response({"map": mymap}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No map found close enough."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)




class FetchMapLinks(APIView):
    authentication_classes = [authentication.SessionAuthentication,authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self,request):
        serializer = MapIdsSerializer(data=request.data,context={"user":request.user})
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
 
