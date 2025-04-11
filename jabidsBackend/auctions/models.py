from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import User
from typing import Optional


class Category(models.Model):
    name: str = models.CharField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering: tuple = ('id',)

    def __str__(self) -> str:
        return self.name


class Auction(models.Model):
    title: str = models.CharField(max_length=150)
    description: str = models.TextField()
    creation_date: timezone.datetime = models.DateTimeField(
        auto_now_add=True, editable=False
    )
    closing_date: timezone.datetime = models.DateTimeField()
    thumbnail: Optional[str] = models.URLField(max_length=200, blank=True)
    starting_price: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2
    )
    stock: int = models.IntegerField(validators=[MinValueValidator(1)])
    rating: models.DecimalField = models.DecimalField(
        max_digits=3, decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    category: Category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='auctions'
    )
    brand: str = models.CharField(max_length=100)
    creator: User = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='auctions'
    )

    @property
    def is_open(self) -> bool:
        return self.closing_date > timezone.now()

    class Meta:
        ordering: tuple = ('id',)

    def __str__(self) -> str:
        return self.title


class Bid(models.Model):
    price: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    creation_date: timezone.datetime = models.DateTimeField(auto_now_add=True)
    bidder_name: str = models.CharField(max_length=100)
    auction_id: int = models.IntegerField()

    class Meta:
        ordering: tuple = ('price',)
        unique_together: tuple = ('price', 'bidder_name', 'auction_id')

    def __str__(self) -> str:
        return f"Bid {self.id} for auction {self.auction_id} by {self.bidder_name}"
