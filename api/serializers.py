from rest_framework import serializers

from gerlumph_maps.models import MagMaps


class ModelInstanceListField(serializers.ListField):

    def __init__(self, queryset, *args, **kwargs):
        self.queryset = queryset
        # Dynamically set up the child type for validation
        kwargs['child'] = serializers.IntegerField()
        super().__init__(*args, **kwargs)
        

    def to_internal_value(self, data):
        # Django REST Framework passes the entire array to this method
        # because we are overriding a ListField directly rather than using many=True
        if not isinstance(data, list):
            raise serializers.ValidationError("Expected a JSON array/list of values.")
            
        if not data:
            return []
        
        
        requested_ids = set(data)
        
        # Fetch the actual database instances matching the IDs
        instances = list(self.queryset.filter(pk__in=requested_ids))
        existing_ids = {inst.pk for inst in instances}
        
        # Calculate exactly which IDs are missing
        missing_ids = requested_ids - existing_ids
        
        if missing_ids:
            missing_str = ", ".join(str(id_) for id_ in sorted(missing_ids))
            raise serializers.ValidationError(
                f"The following IDs do not exist in the database: [{missing_str}]. Contact the admins!"
            )
        
        return instances


    
class MapIdsSerializer(serializers.Serializer):
    ids = ModelInstanceListField(
        queryset=MagMaps.objects.all(),
    )
    
    def validate(self, data):
        ### Check user limits

        if self.context['user']:
            N_maps = len(data.get("ids"))
            check = self.context['user'].limitsandroles.check_all_limits(N_maps)
            if check["errors"]:
                for error in check["errors"]:
                    raise serializers.ValidationError(error)
        else:
            raise serializers.ValidationError("User is not defined, something went wrong!")
                
        return data
