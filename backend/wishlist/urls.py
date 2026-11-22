from django.urls import path

from .views import WishlistAddView, WishlistItemView, WishlistMoveToCartView, WishlistView

urlpatterns = [
    path("", WishlistView.as_view(), name="wishlist"),
    path("add/", WishlistAddView.as_view(), name="wishlist-add"),
    path("items/<int:item_id>/", WishlistItemView.as_view(), name="wishlist-item"),
    path(
        "items/<int:item_id>/move-to-cart/",
        WishlistMoveToCartView.as_view(),
        name="wishlist-move-to-cart",
    ),
]
