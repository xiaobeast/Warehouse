from django.shortcuts import render
from .models import Item

# Create your views here.
def index(request):
    latest_item = Item.objects.order_by('-location')[:5]
    return render(request,'inventory/index.html',
                  {'latest_item':latest_item}
                  )
