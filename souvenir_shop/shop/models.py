from django.db import models
from django.utils import timezone

class Artist(models.Model):
    """
    Represents an artist who provides items to the shop.
    """
    name = models.CharField(max_length=200, verbose_name="Artist Name")
    contact_information = models.TextField(verbose_name="Contact Info")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Artist"
        verbose_name_plural = "Artists"

class Product(models.Model):
    """
    Represents an item sold in the shop.
    """
    name = models.CharField(max_length=200, verbose_name="Product Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Purchase Price")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price")
    stock_quantity = models.IntegerField(default=0, verbose_name="Stock Quantity")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="products", verbose_name="Artist")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

class Purchase(models.Model):
    """
    Represents a purchase of items from an artist.
    """
    purchase_date = models.DateTimeField(default=timezone.now, verbose_name="Purchase Date")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="purchases", verbose_name="Artist")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Amount")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    def __str__(self):
        return f"Purchase from {self.artist} on {self.purchase_date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"

class PurchaseItem(models.Model):
    """
    Represents a specific item within a purchase.  Links Purchase and Product.
    """
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items", verbose_name="Purchase")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="purchase_items", verbose_name="Product")
    quantity = models.IntegerField(verbose_name="Quantity")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Unit Price")

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Purchase {self.purchase.id}"

    class Meta:
        verbose_name = "Purchase Item"
        verbose_name_plural = "Purchase Items"
        unique_together = ('purchase', 'product')  # Prevents duplicate items in a purchase

class Sale(models.Model):
    """
    Represents a sale of items to a customer.
    """
    sale_date = models.DateTimeField(default=timezone.now, verbose_name="Sale Date")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Amount")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    def __str__(self):
        return f"Sale on {self.sale_date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

class SaleItem(models.Model):
    """
    Represents a specific item within a sale. Links Sale and Product.
    """
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items", verbose_name="Sale")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sale_items", verbose_name="Product")
    quantity = models.IntegerField(verbose_name="Quantity")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Unit Price")

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Sale {self.sale.id}"

    class Meta:
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"
        unique_together = ('sale', 'product') # Prevents duplicate items in a sale

class Transaction(models.Model):
    """
    Represents a financial transaction (purchase, sale, expense, etc.).
    """
    TRANSACTION_TYPES = (
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),
        ('ADJUSTMENT', 'Adjustment'),  # For manual balance changes
    )
    transaction_date = models.DateTimeField(default=timezone.now, verbose_name="Transaction Date")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="Transaction Type")
    description = models.CharField(max_length=200, verbose_name="Description")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount")  # Positive for income, negative for expense
    related_purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions", verbose_name="Related Purchase")
    related_sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions", verbose_name="Related Sale")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    def __str__(self):
        return f"{self.transaction_type} on {self.transaction_date.strftime('%Y-%m-%d')}: {self.description}"

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

class Balance(models.Model):
    """
    Represents the shop's balance at a specific point in time.
    """
    balance_date = models.DateField(default=timezone.now().date(), unique=True, verbose_name="Balance Date")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    def __str__(self):
        return f"Balance on {self.balance_date.strftime('%Y-%m-%d')}: {self.amount}"

    class Meta:
        verbose_name = "Balance"
        verbose_name_plural = "Balances"
