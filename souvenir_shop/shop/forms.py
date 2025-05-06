from django import forms
from .models import Artist, Product, Purchase, PurchaseItem, Sale, SaleItem, Transaction

class ArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['name', 'contact_information', 'notes']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'purchase_price', 'selling_price', 'stock_quantity', 'artist']

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['artist', 'notes']

class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'unit_price': forms.NumberInput(attrs={'readonly': 'readonly'}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['notes']

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'unit_price': forms.NumberInput(attrs={'readonly': 'readonly'}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'description', 'amount', 'related_purchase', 'related_sale', 'notes']
        widgets = {
            'transaction_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }