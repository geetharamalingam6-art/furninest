from django.urls import path

from .views import CheckoutSummaryView, CheckoutView, OrderDetailView, OrderListView

urlpatterns = [
    path("checkout/summary/", CheckoutSummaryView.as_view(), name="checkout-summary"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("", OrderListView.as_view(), name="order-list"),
    path("<int:order_id>/", OrderDetailView.as_view(), name="order-detail"),
]
