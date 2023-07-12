from rest_framework.views import APIView, Request, Response, status
from rest_framework.pagination import PageNumberPagination
from .models import Pet
from groups.models import Group
from traits.models import Trait
from .serializers import PetSerializer
from django.shortcuts import get_object_or_404


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        pets = Pet.objects.all()

        trait = request.query_params.get("trait", None)

        if trait:
            pets = pets.filter(traits__name__icontains=trait)

        result_page = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        group_data = serializer.validated_data.pop("group")
        traits_data = serializer.validated_data.pop("traits")

        group = Group.objects.filter(scientific_name__iexact=group_data["scientific_name"]).first()

        if not group:
            group = Group.objects.create(**group_data)

        pet = Pet.objects.create(**serializer.validated_data, group=group)

        for trait in traits_data:
            trait_dict = Trait.objects.filter(name__iexact=trait["name"]).first()

            if not trait_dict:
                trait_dict = Trait.objects.create(**trait)

            pet.traits.add(trait_dict)

        serializer = PetSerializer(instance=pet)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PetInfosView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(instance=pet)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        serializer = PetSerializer(data=request.data, partial=True)

        pet = get_object_or_404(Pet, id=pet_id)

        serializer.is_valid(raise_exception=True)

        if "group" in request.data:
            group_data = serializer.validated_data.pop("group")

            group = Group.objects.filter(scientific_name__iexact=group_data["scientific_name"]).first()

            if not group:
                group = Group.objects.create(**group_data)

            pet.group = group

        if "traits" in request.data:
            traits_data = serializer.validated_data.pop("traits")

            for trait in traits_data:
                trait_dict = Trait.objects.filter(name__iexact=trait["name"]).first()

                if not trait_dict:
                    trait_dict = Trait.objects.create(**trait)
                pet.traits.clear()
                pet.traits.add(trait_dict)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        pet.save()

        serializer = PetSerializer(instance=pet)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
