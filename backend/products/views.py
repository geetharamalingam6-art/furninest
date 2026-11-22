from django.db.models import Avg, Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Brand, Category, Product
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Category.objects.filter(is_active=True)
            .annotate(product_count=Count("products", filter=Q(products__is_active=True)))
            .order_by("name")
        )


class BrandListView(ListAPIView):
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Brand.objects.filter(is_active=True).order_by("name")


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    filterset_fields = {
        "category__slug": ["exact"],
        "brand__slug": ["exact"],
        "material": ["exact"],
        "color": ["exact"],
        "price": ["gte", "lte"],
        "stock_quantity": ["gt"],
        "is_featured": ["exact"],
    }
    search_fields = ["name", "description", "category__name", "brand__name"]
    ordering_fields = ["price", "created_at", "average_rating"]

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, category__is_active=True)
            .select_related("category", "brand")
            .prefetch_related("images")
            .annotate(
                average_rating=Avg(
                    "reviews__rating",
                    filter=Q(reviews__is_visible=True),
                ),
                review_count=Count(
                    "reviews",
                    filter=Q(reviews__is_visible=True),
                    distinct=True,
                ),
            )
            .order_by("-created_at")
        )

    @action(detail=False, methods=["get"], url_path="featured")
    def featured(self, request):
        products = self.filter_queryset(self.get_queryset().filter(is_featured=True))
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(products, many=True).data)
