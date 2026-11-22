from django.urls import path

from .views import DashboardOrderListView, DashboardOrderStatusView, DashboardOverviewView

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("orders/", DashboardOrderListView.as_view(), name="dashboard-orders"),
    path(
        "orders/<int:order_id>/status/",
        DashboardOrderStatusView.as_view(),
        name="dashboard-order-status",
    ),
]
