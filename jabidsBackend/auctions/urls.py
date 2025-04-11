from django.urls import path, include
from .views import (
    AuctionListCreateView,
    AuctionDetailView,
    CategoryListView,
    CategoryDetailView,
    BidListCreateView,
    BidDetailView,
)

app_name = 'auctions'
urlpatterns = [
    path('', AuctionListCreateView.as_view(), name='auction-list-create'),
    path('<int:pk>/', AuctionDetailView.as_view(), name='auction-detail'),

    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('category/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),

    # Bids
    path('<int:auction_id>/bids/', BidListCreateView.as_view(), name='bid-list'),
    path('<int:auction_id>/bids/<int:pk>/', BidDetailView.as_view(), name='bid-detail'),
]
