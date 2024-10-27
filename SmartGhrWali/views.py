import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, Category, Purchase, Usage
from django.utils.timezone import timedelta, now
from.forms import PurchaseForm, UsageForm
from django.db.models import Prefetch
from django.contrib import messages
import logging

# Create your views here.

def index(request):
    return render(request, 'index.html')

def dashboard(request):
    categories = Category.objects.prefetch_related(Prefetch('item_set', queryset=Item.objects.filter(user=request.user)))
    return render(request, 'dashboard.html', {'categories': categories})

def purchases(request):
    today = now().date()
    # Fetch purchases made by the current user in the last 30 days
    purchases = Purchase.objects.filter(user=request.user,purchased_on__gte=today - timedelta(days=30)).order_by('-purchased_on')

    if request.method == 'POST':
        form = PurchaseForm(request.POST, user=request.user)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.user = request.user  # Associate the purchase with the current user
            purchase.save()
            messages.success(request, 'Purchase has been added successfully!')
            return redirect('purchases')  # Redirect to a 'purchases' page or wherever you want
    else:
        form = PurchaseForm()

    context = {
        'form': form,
        'purchases': purchases,
    }
    
    return render(request, 'purchases.html', context)

def delete_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    purchase.delete()
    messages.success(request, 'Purchase has been deleted successfully!')
    return redirect('purchases')

def usages(request):
    today = now().date()
    # Fetch purchases made by the current user in the last 30 days
    usages = Usage.objects.filter(user=request.user,used_on__gte=today - timedelta(days=30)).order_by('-used_on')

    if request.method == 'POST':
        form = UsageForm(request.POST)
        if form.is_valid():
            usage = form.save(commit=False)
            usage.user = request.user  # Associate the purchase with the current user
            usage.save()
            messages.success(request, 'Usage has been added successfully!')
            return redirect('usages')  # Redirect to a 'purchases' page or wherever you want
    else:
        form = UsageForm()

    context = {
        'form': form,
        'usages': usages,
    }
    
    return render(request, 'usages.html', context)

def delete_usage(request, usage_id):
    usage = get_object_or_404(Usage, id=usage_id, user=request.user)
    usage.delete()
    messages.success(request, 'Usage has been deleted successfully!')
    return redirect('usages')


def recipe_page(request):
    return render(request, "recipes.html")



logger = logging.getLogger(__name__)

def fetch_recipes(request):
    if request.method == "POST":
        selected_item_ids = request.POST.getlist("selected_items")

        # Check if any items were selected
        if not selected_item_ids:
            return render(request, "recipes.html", {"error": "No ingredients selected."})

        ingredients = ",".join(
            item.name for item in Item.objects.filter(id__in=selected_item_ids)
        )

        url = "https://api.edamam.com/search"

        try:
            response = requests.get(
                url,
                params={
                    "q": ingredients,
                    "app_id": settings.EDAMAM_APP_ID,
                    "app_key": settings.EDAMAM_APP_KEY,
                    "from": 0,
                    "to": 5,  # Limit the number of recipes
                },
            )
            response.raise_for_status()  # Raise an error if the request fails
            data = response.json()

            # Handle cases where the data structure might not be as expected
            recipes = [
                {
                    "title": recipe["recipe"].get("label", "No Title"),
                    "ingredients": ", ".join([ing["food"] for ing in recipe["recipe"].get("ingredients", [])]),
                    "link": recipe["recipe"].get("url", "#"),
                }
                for recipe in data.get("hits", [])
            ]
            return render(request, "recipes.html", {"recipes": recipes})

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching recipes: {e}")
            return render(request, "recipes.html", {"error": "Failed to fetch recipes."})

    return redirect("dashboard")  # Redirect to dashboard or any appropriate view