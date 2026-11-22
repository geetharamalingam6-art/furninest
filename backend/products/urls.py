from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BrandListView, CategoryListView, ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("", include(router.urls)),
]
