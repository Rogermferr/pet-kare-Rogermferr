from django.urls import path
from .views import PetView, PetInfosView

urlpatterns = [path("pets/", PetView.as_view()), path("pets/<int:pet_id>/", PetInfosView.as_view())]
