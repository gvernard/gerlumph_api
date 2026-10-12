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



class HealthCheck(APIView):
    authentication_classes = [authentication.SessionAuthentication,authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self,request):
        #try:
        #    connection.ensure_connection()
        #except Exception:
        #    return JsonResponse({"status": "unhealthy", "database": "down"}, status=500)
        return Response({"status": "healthy"}, status=200)



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
                ds=Abs(
                    F('s')-s0,
                    output_field=FloatField()
                ),
            ).filter(
                dkg__lt=dkg_tol
            ).order_by(
                'dkg','ds'
            )

            map_obj = match_qset.first()
            if map_obj:
                mymap = {}
                mymap["id"] = map_obj.id
                mymap["k"] = map_obj.kappa
                mymap["g"] = map_obj.gamma
                mymap["s"] = map_obj.s
                mymap["ds"] = map_obj.ds
                mymap["dkg"] = map_obj.dkg
                mymap["res"] = map_obj.res
                mymap["width"] = map_obj.width
                return Response({"map": mymap,"message": "success"}, status=status.HTTP_200_OK)
            else:
                return Response({"map": '', "message": "No map found close enough."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)




class FetchMapLinks(APIView):
    authentication_classes = [authentication.SessionAuthentication,authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self,request):
        serializer = MapIdsSerializer(data=request.data,context={"user":request.user})
        if serializer.is_valid():
            maps = serializer.validated_data["ids"]

            map_links = []
            meta_links = []
            for mappa in maps:
                map_links.append( mappa.get_file_url("map.bin") )
                meta_links.append( mappa.get_file_url("mapmeta.dat") )


            new_download = Downloads.objects.create(owner=request.user)
            new_download.maps.set(maps)            
                
            return Response({"map_links": map_links,"meta_links": meta_links, "message": "success"}, status=status.HTTP_200_OK)
        else:
            error = serializer.errors["ids"]
            return Response({"map_links": '',"meta_links": '', "message": error},status=status.HTTP_400_BAD_REQUEST)
 
