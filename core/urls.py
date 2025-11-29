from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    ProduceListView, ProcurementListView, ProcurementCreateView, ProcurementUpdateView, ProcurementDeleteView,
    SaleListView, SaleCreateView, SaleUpdateView, SaleDeleteView, ReceiptDownloadView,
    StockListView, StockUpdateView,
    AnalyticsKPIsView, AnalyticsTrendsView
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    # Produce
    path('produce/list/', ProduceListView.as_view(), name='produce_list'),
    # Procurement
    path('procurement/list/', ProcurementListView.as_view(), name='procurement_list'),
    path('procurement/create/', ProcurementCreateView.as_view(), name='procurement_create'),
    path('procurement/update/<int:pk>/', ProcurementUpdateView.as_view(), name='procurement_update'),
    path('procurement/delete/<int:pk>/', ProcurementDeleteView.as_view(), name='procurement_delete'),
    # Sales
    path('sales/list/', SaleListView.as_view(), name='sale_list'),
    path('sales/create/', SaleCreateView.as_view(), name='sale_create'),
    path('sales/update/<int:pk>/', SaleUpdateView.as_view(), name='sale_update'),
    path('sales/delete/<int:pk>/', SaleDeleteView.as_view(), name='sale_delete'),
    path('sales/receipt/<str:receipt_id>/', ReceiptDownloadView.as_view(), name='receipt_download'),
    # Stock
    path('stock/list/', StockListView.as_view(), name='stock_list'),
    path('stock/update/<int:pk>/', StockUpdateView.as_view(), name='stock_update'),
    # Analytics
    path('analytics/kpis/', AnalyticsKPIsView.as_view(), name='kpis'),
    path('analytics/trends/', AnalyticsTrendsView.as_view(), name='trends'),
]