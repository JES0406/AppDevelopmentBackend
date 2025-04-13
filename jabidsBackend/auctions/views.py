from django.shortcuts import render
from rest_framework import generics, status
from .models import Auction, Category, Bid
from .serializers import (
    AuctionSerializer,
    AuctionDetailSerializer,
    CategorySerializer,
    BidSerializer,
)
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django.db.models import OuterRef, Subquery, DecimalField, F
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from .permissions import IsOwnerOrAdmin  # Your custom permission



class BaseListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()


class AuctionListCreateView(BaseListCreateView):
    serializer_class = AuctionSerializer

    def get_queryset(self):
        queryset = Auction.objects.all()

        # Text filter
        text = self.request.query_params.get('text')
        if text:
            queryset = queryset.filter(
                Q(title__icontains=text) |
                Q(description__icontains=text)
            )

        # Category filter
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name__icontains=category)

        # Subquery to get highest bid per auction
        highest_bid_subquery = Bid.objects.filter(
            auction=OuterRef('pk')
        ).order_by('-price').values('price')[:1]

        # Use Coalesce so that auctions with no bids fall back to starting_price
        queryset = queryset.annotate(
            current_price=Coalesce(
                Subquery(highest_bid_subquery, output_field=DecimalField()),
                F('starting_price')
            )
        )

        # Min price filter
        min_price = self.request.query_params.get('min_price')
        if min_price:
            try:
                min_price = float(min_price)
            except ValueError:
                raise ValidationError("Min price must be a number.")
            if min_price < 0:
                raise ValidationError("Min price must be greater than or equal to 0.")
            queryset = queryset.filter(current_price__gte=min_price)

        # Max price filter
        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                max_price = float(max_price)
            except ValueError:
                raise ValidationError("Max price must be a number.")
            if min_price and max_price < min_price:
                raise ValidationError("Max price must be greater than min price.")
            if max_price < 0:
                raise ValidationError("Max price must be greater than or equal to 0.")
            queryset = queryset.filter(current_price__lte=max_price)

        return queryset

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class AuctionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AuctionDetailSerializer
    queryset = Auction.objects.all()


class CategoryListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class BidListCreateView(BaseListCreateView):
    serializer_class = BidSerializer

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return Bid.objects.filter(auction_id=auction_id).order_by('-price')

    def perform_create(self, serializer):
        auction_id = self.kwargs['auction_id']
        serializer.save(auction_id=auction_id, bidder_name=self.request.user.username)



class BidDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        bid = self.get_object()

        # Check auction state
        try:
            auction = Auction.objects.get(id=bid.auction_id)
        except Auction.DoesNotExist:
            return Response({"detail": "Associated auction not found."},
                            status=status.HTTP_404_NOT_FOUND)

        if not auction.is_open:
            return Response({"detail": "Cannot edit bid. Auction is closed."},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        bid = self.get_object()

        # Check auction state
        try:
            auction = Auction.objects.get(id=bid.auction_id)
        except Auction.DoesNotExist:
            return Response({"detail": "Associated auction not found."},
                            status=status.HTTP_404_NOT_FOUND)

        if not auction.is_open:
            return Response({"detail": "Cannot delete bid. Auction is closed."},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().destroy(request, *args, **kwargs)
