from django.urls import path
from . import views


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
app_name = 'api'
urlpatterns = [
    path('fetch-maps/',views.FetchMapLinks.as_view(), name="fetch-maps"),
]
