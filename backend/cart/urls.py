from django.urls import path

from .views import CartAddView, CartClearView, CartItemView, CartView

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("add/", CartAddView.as_view(), name="cart-add"),
    path("clear/", CartClearView.as_view(), name="cart-clear"),
    path("items/<int:item_id>/", CartItemView.as_view(), name="cart-item"),
]
