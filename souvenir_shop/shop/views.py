from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone
from .models import Artist, Product, Purchase, PurchaseItem, Sale, SaleItem, Transaction, Balance
from .forms import ArtistForm, ProductForm, PurchaseForm, PurchaseItemForm, SaleForm, SaleItemForm, TransactionForm

# Artist Views
def artist_list(request):
    artists = Artist.objects.all()
    return render(request, 'shop/artist_list.html', {'artists': artists})

def artist_create(request):
    if request.method == 'POST':
        form = ArtistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shop:artist_list')
    else:
        form = ArtistForm()
    return render(request, 'shop/artist_form.html', {'form': form, 'title': 'Add Artist'})

def artist_update(request, pk):
    artist = get_object_or_404(Artist, pk=pk)
    if request.method == 'POST':
        form = ArtistForm(request.POST, instance=artist)
        if form.is_valid():
            form.save()
            return redirect('shop:artist_list')
    else:
        form = ArtistForm(instance=artist)
    return render(request, 'shop/artist_form.html', {'form': form, 'title': 'Edit Artist'})

def artist_delete(request, pk):
    artist = get_object_or_404(Artist, pk=pk)
    if request.method == 'POST':
        artist.delete()
        return redirect('shop:artist_list')
    return render(request, 'shop/artist_delete.html', {'artist': artist})

# Product Views
def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})

def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shop:product_list')
    else:
        form = ProductForm()
    return render(request, 'shop/product_form.html', {'form': form, 'title': 'Add Product'})

def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('shop:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/product_form.html', {'form': form, 'title': 'Edit Product'})

def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('shop:product_list')
    return render(request, 'shop/product_delete.html', {'product': product})

# Purchase Views
def purchase_list(request):
    purchases = Purchase.objects.all().order_by('-purchase_date')
    return render(request, 'shop/purchase_list.html', {'purchases': purchases})

PurchaseItemFormSet = inlineformset_factory(Purchase, PurchaseItem, form=PurchaseItemForm, extra=1, can_delete=False)

@transaction.atomic
def purchase_create(request):
    if request.method == 'POST':
        purchase_form = PurchaseForm(request.POST)
        formset = PurchaseItemFormSet(request.POST)
        if purchase_form.is_valid() and formset.is_valid():
            purchase = purchase_form.save()
            total_amount = 0
            for form in formset:
                if form.cleaned_data:  # Make sure the form isn't empty
                    purchase_item = form.save(commit=False)
                    purchase_item.purchase = purchase
                    purchase_item.unit_price = purchase_item.product.purchase_price  # Set unit price
                    purchase_item.save()
                    total_amount += purchase_item.quantity * purchase_item.unit_price
                    # Update product stock
                    purchase_item.product.stock_quantity += purchase_item.quantity
                    purchase_item.product.save()

            purchase.total_amount = total_amount
            purchase.save()

            # Create Transaction
            Transaction.objects.create(
                transaction_type='PURCHASE',
                description=f'Purchase from {purchase.artist.name} on {purchase.purchase_date.strftime("%Y-%m-%d")}',
                amount=-total_amount,  # Negative for purchase
                related_purchase=purchase,
                transaction_date=purchase.purchase_date
            )
            update_or_create_balance()
            return redirect('shop:purchase_list')
        else:
            print(purchase_form.errors) #For Debugging
            print(formset.errors)
    else:
        purchase_form = PurchaseForm()
        formset = PurchaseItemFormSet()
    return render(request, 'shop/purchase_form.html', {'purchase_form': purchase_form, 'formset': formset, 'title': 'Add Purchase'})


def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    return render(request, 'shop/purchase_detail.html', {'purchase': purchase})

def purchase_update(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    PurchaseItemFormSet = inlineformset_factory(Purchase, PurchaseItem, form=PurchaseItemForm, extra=1, can_delete=True)

    if request.method == 'POST':
        purchase_form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseItemFormSet(request.POST, instance=purchase)

        with transaction.atomic():
            if purchase_form.is_valid() and formset.is_valid():
                purchase = purchase_form.save()

                # Calculate the new total amount
                total_amount = 0
                for form in formset:
                    if form.cleaned_data:
                        purchase_item = form.save(commit=False)
                        purchase_item.purchase = purchase
                        purchase_item.unit_price = purchase_item.product.purchase_price
                        purchase_item.save()
                        total_amount += purchase_item.quantity * purchase_item.unit_price
                    elif form.instance.pk: #Check if the instance has a primary key
                         form.instance.delete()

                purchase.total_amount = total_amount
                purchase.save()

                # Update stock quantities.  This is complex, need to find changes.
                original_items = {item.product.id: item.quantity for item in purchase.items.all()}
                new_items = {}
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        product_id = form.cleaned_data['product'].id
                        quantity = form.cleaned_data['quantity']
                        new_items[product_id] = quantity

                for product_id, new_quantity in new_items.items():
                    original_quantity = original_items.get(product_id, 0)
                    product = Product.objects.get(pk=product_id)
                    product.stock_quantity += (new_quantity - original_quantity)
                    product.save()
                for product_id, original_quantity in original_items.items():
                    if product_id not in new_items: #Item was deleted
                         product = Product.objects.get(pk=product_id)
                         product.stock_quantity -= original_quantity
                         product.save()

                # Update Transaction
                # Get the existing transaction, or create a new one if it doesn't exist
                transaction, created = Transaction.objects.get_or_create(
                    related_purchase=purchase,
                    defaults={
                        'transaction_type': 'PURCHASE',
                        'description': f'Purchase from {purchase.artist.name} on {purchase.purchase_date.strftime("%Y-%m-%d")}',
                        'amount': -total_amount,
                        'transaction_date': purchase.purchase_date,
                    }
                )
                if not created:
                    transaction.amount = -total_amount
                    transaction.description = f'Purchase from {purchase.artist.name} on {purchase.purchase_date.strftime("%Y-%m-%d")}'
                    transaction.save()
                update_or_create_balance()
                return redirect('shop:purchase_list')
            else:
                print(purchase_form.errors)
                print(formset.errors)
    else:
        purchase_form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(instance=purchase)

    return render(request, 'shop/purchase_form.html', {'purchase_form': purchase_form, 'formset': formset, 'title': 'Edit Purchase'})

def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            # Reverse stock changes
            for item in purchase.items.all():
                item.product.stock_quantity -= item.quantity
                item.product.save()
            # Delete related transaction
            Transaction.objects.filter(related_purchase=purchase).delete()
            purchase.delete()
            update_or_create_balance()
        return redirect('shop:purchase_list')
    return render(request, 'shop/purchase_delete.html', {'purchase': purchase})

# Sale Views
def sale_list(request):
    sales = Sale.objects.all().order_by('-sale_date')
    return render(request, 'shop/sale_list.html', {'sales': sales})

SaleItemFormSet = inlineformset_factory(Sale, SaleItem, form=SaleItemForm, extra=1, can_delete=False)

@transaction.atomic
def sale_create(request):
    if request.method == 'POST':
        sale_form = SaleForm(request.POST)
        formset = SaleItemFormSet(request.POST)
        if sale_form.is_valid() and formset.is_valid():
            sale = sale_form.save()
            total_amount = 0
            for form in formset:
                if form.cleaned_data:
                    sale_item = form.save(commit=False)
                    sale_item.sale = sale
                    sale_item.unit_price = sale_item.product.selling_price  # Set unit price
                    sale_item.save()
                    total_amount += sale_item.quantity * sale_item.unit_price
                    # Update product stock
                    sale_item.product.stock_quantity -= sale_item.quantity
                    sale_item.product.save()

            sale.total_amount = total_amount
            sale.save()
             # Create Transaction
            Transaction.objects.create(
                transaction_type='SALE',
                description=f'Sale on {sale.sale_date.strftime("%Y-%m-%d")}',
                amount=total_amount,  # Positive for sale
                related_sale=sale,
                transaction_date=sale.sale_date
            )
            update_or_create_balance()
            return redirect('shop:sale_list')
        else:
            print(sale_form.errors)
            print(formset.errors)
    else:
        sale_form = SaleForm()
        formset = SaleItemFormSet()
    return render(request, 'shop/sale_form.html', {'sale_form': sale_form, 'formset': formset, 'title': 'Add Sale'})

def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'shop/sale_detail.html', {'sale': sale})

def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    SaleItemFormSet = inlineformset_factory(Sale, SaleItem, form=SaleItemForm, extra=1, can_delete=True)

    if request.method == 'POST':
        sale_form = SaleForm(request.POST, instance=sale)
        formset = SaleItemFormSet(request.POST, instance=sale)

        with transaction.atomic():
            if sale_form.is_valid() and formset.is_valid():
                sale = sale_form.save()
                total_amount = 0
                for form in formset:
                    if form.cleaned_data:
                        sale_item = form.save(commit=False)
                        sale_item.sale = sale
                        sale_item.unit_price = sale_item.product.selling_price
                        sale_item.save()
                        total_amount += sale_item.quantity * sale_item.unit_price
                    elif form.instance.pk:
                         form.instance.delete()

                sale.total_amount = total_amount
                sale.save()

                # Update stock quantities.
                original_items = {item.product.id: item.quantity for item in sale.items.all()}
                new_items = {}
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        product_id = form.cleaned_data['product'].id
                        quantity = form.cleaned_data['quantity']
                        new_items[product_id] = quantity

                for product_id, new_quantity in new_items.items():
                    original_quantity = original_items.get(product_id, 0)
                    product = Product.objects.get(pk=product_id)
                    product.stock_quantity += (original_quantity - new_quantity)
                    product.save()
                for product_id, original_quantity in original_items.items():
                    if product_id not in new_items:
                         product = Product.objects.get(pk=product_id)
                         product.stock_quantity += original_quantity
                         product.save()
                # Update Transaction
                transaction, created = Transaction.objects.get_or_create(
                    related_sale=sale,
                    defaults={
                        'transaction_type': 'SALE',
                        'description': f'Sale on {sale.sale_date.strftime("%Y-%m-%d")}',
                        'amount': total_amount,
                        'transaction_date': sale.sale_date,
                    }
                )
                if not created:
                    transaction.amount = total_amount
                    transaction.description = f'Sale on {sale.sale_date.strftime("%Y-%m-%d")}'
                    transaction.save()
                update_or_create_balance()
                return redirect('shop:sale_list')
            else:
                print(sale_form.errors)
                print(formset.errors)
    else:
        sale_form = SaleForm(instance=sale)
        formset = SaleItemFormSet(instance=sale)
    return render(request, 'shop/sale_form.html', {'sale_form': sale_form, 'formset': formset, 'title': 'Edit Sale'})

def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            # Reverse stock changes
            for item in sale.items.all():
                item.product.stock_quantity += item.quantity
                item.product.save()
            # Delete related transaction
            Transaction.objects.filter(related_sale=sale).delete()
            sale.delete()
            update_or_create_balance()
        return redirect('shop:sale_list')
    return render(request, 'shop/sale_delete.html', {'sale': sale})

# Transaction Views
def transaction_list(request):
    transactions = Transaction.objects.all().order_by('-transaction_date')
    return render(request, 'shop/transaction_list.html', {'transactions': transactions})

def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            update_or_create_balance()
            return redirect('shop:transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'shop/transaction_form.html', {'form': form, 'title': 'Add Transaction'})

def transaction_update(request, pk):
    transaction_obj = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction_obj)
        if form.is_valid():
            form.save()
            update_or_create_balance()
            return redirect('shop:transaction_list')
    else:
        form = TransactionForm(instance=transaction_obj)
    return render(request, 'shop/transaction_form.html', {'form': form, 'title': 'Edit Transaction'})

def transaction_delete(request, pk):
    transaction_obj = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        transaction_obj.delete()
        update_or_create_balance()
        return redirect('shop:transaction_list')
    return render(request, 'shop/transaction_delete.html', {'transaction': transaction_obj})

# Balance Views
def balance_list(request):
    balances = Balance.objects.all().order_by('-balance_date')
    current_balance = get_current_balance()
    return render(request, 'shop/balance_list.html', {'balances': balances, 'current_balance': current_balance})

def get_current_balance():
    """
    Calculates the current balance by summing all transactions up to today.
    """
    today = timezone.now().date()
    # Get the latest balance, and use that as a starting point.
    latest_balance = Balance.objects.order_by('-balance_date').first()
    if latest_balance:
        current_balance = latest_balance.amount
        # Add transactions since the latest balance date
        transactions = Transaction.objects.filter(transaction_date__date__gt=latest_balance.balance_date, transaction_date__date__lte=today).aggregate(Sum('amount'))['amount__sum'] or 0
        current_balance += transactions
    else:
        # No previous balance, so start from zero.
        current_balance = Transaction.objects.filter(transaction_date__date__lte=today).aggregate(Sum('amount'))['amount__sum'] or 0

    return current_balance
def update_or_create_balance():
    """
    Updates the current balance or creates a new balance entry for today.
    """
    today = timezone.now().date()
    current_balance = get_current_balance()

    # Check if a balance entry for today already exists
    balance, created = Balance.objects.get_or_create(balance_date=today, defaults={'amount': current_balance})
    if not created:
        # Update the existing balance entry
        balance.amount = current_balance
        balance.save()
# KPI Dashboard View
def dashboard(request):
    """
    View for the KPI dashboard.
    """
    # Total Sales Revenue (last 7 days)
    sales_last_7_days = Sale.objects.filter(sale_date__gte=timezone.now() - timezone.timedelta(days=7)).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Total Sales Revenue (last 30 days)
    sales_last_30_days = Sale.objects.filter(sale_date__gte=timezone.now() - timezone.timedelta(days=30)).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Top Selling Products (last 30 days)
    top_selling_products = SaleItem.objects.filter(sale__sale_date__gte=timezone.now() - timezone.timedelta(days=30)).values('product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]

    # Low Stock Items (items with stock less than 5)
    low_stock_products = Product.objects.filter(stock_quantity__lt=5)

    # Profit Margin (Overall)
    total_sales = Sale.objects.all().aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_purchases = Purchase.objects.all().aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    overall_profit_margin = total_sales - total_purchases

    # Balance History (last 30 days)
    balance_history = Balance.objects.filter(balance_date__gte=timezone.now().date() - timezone.timedelta(days=30)).order_by('balance_date')
    balance_dates = [b.balance_date.strftime('%Y-%m-%d') for b in balance_history]
    balance_amounts = [float(b.amount) for b in balance_history]


    context = {
        'sales_last_7_days': sales_last_7_days,
        'sales_last_30_days': sales_last_30_days,
        'top_selling_products': top_selling_products,
        'low_stock_products': low_stock_products,
        'overall_profit_margin': overall_profit_margin,
        'balance_dates': balance_dates,
        'balance_amounts': balance_amounts,
    }
    return render(request, 'shop/dashboard.html', context)
