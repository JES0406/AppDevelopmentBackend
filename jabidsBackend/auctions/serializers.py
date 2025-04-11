from rest_framework import serializers
from .models import Auction, Category, Bid
from django.utils import timezone
from datetime import timedelta


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', )


class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class BaseAuctionSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True
    )
    closing_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    is_open = serializers.BooleanField(read_only=True)

    def validate_closing_date(self, value):
        now = timezone.now()
        if value <= now:
            raise serializers.ValidationError("Closing date must be in the future.")
        if value < now + timedelta(days=15):
            raise serializers.ValidationError(
                "Closing date must be at least 15 days from now."
            )
        return value

    class Meta:
        model = Auction
        fields = '__all__'


class AuctionSerializer(BaseAuctionSerializer):
    class Meta:
        model = Auction
        fields = (
            'id', 'title', 'closing_date', 'thumbnail',
            'starting_price', 'is_open'
        )


class AuctionDetailSerializer(BaseAuctionSerializer):
    class Meta:
        model = Auction
        fields = '__all__'
        read_only_fields = ('creation_date', 'is_open', 'id')


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ('id', 'price', 'creation_date', 'bidder_name', 'auction_id')
        read_only_fields = ('creation_date', )

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")

        auction_id = self.validated_data.get('auction_id')
        if auction_id:
            try:
                auction = Auction.objects.get(id=auction_id)
            except Auction.DoesNotExist:
                raise serializers.ValidationError("Auction does not exist.")

            if not auction.is_open:
                raise serializers.ValidationError(
                    "Auction is closed. Cannot place a bid."
                )

            highest_bid = Bid.objects.filter(
                auction_id=auction_id
            ).order_by('-price').first()

            if highest_bid and value <= highest_bid.price:
                raise serializers.ValidationError(
                    "Bid must be higher than the current highest bid."
                )

        return value
