import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect
import time
# Create your views here.

from ecommerce.forms import OrderForm
from ecommerce.models import LineOrder

User = get_user_model()

def home(request):
    form = OrderForm() 
    return render(request, "home.html", {"form": form}) 

# new purchase POST request view ⬇️
@require_POST
def purchase(request):
    form = OrderForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        # TODO - add stripe integration to process the order
        # for now, just wait for 2 seconds to simulate the processing
        time.sleep(2)
    return render(request, "product.html", {"form": form})

@require_POST
def purchase(request):
    form = OrderForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
 
        # replace time.sleep(2) with the following code ⬇️
 
        # 1 - set stripe api key
        stripe.api_key = settings.STRIPE_SECRET_KEY
 
        # 2 - create success url
        success_url = (
            request.build_absolute_uri(
                reverse("purchase_success")
            )
            + "?session_id={CHECKOUT_SESSION_ID}"
        )
 
        # 3 - create cancel url
        cancel_url = request.build_absolute_uri(reverse("home"))
 
        # 4 - create checkout session
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_ID,
                    "quantity": quantity,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url
        )
 
        # 5 - redirect to checkout session url
        return HttpResponseClientRedirect(checkout_session.url)
    return render(request, "product.html", {"form": form})

def purchase_success(request):
    session_id = request.GET.get("session_id")
    if session_id is None:
	      return redirect("home")
 
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        messages.error(request, "There was a problem while buying your product. Please try again.")
        return redirect("home")
    return render(request, "purchase_success.html")

@csrf_exempt
def webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    sig_header = request.headers.get('stripe-signature')
    payload = request.body
    event = None
    try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)
 
    # Handle the checkout.session.completed event
    if event.type == "checkout.session.completed":
        # TODO: create line orders
        return HttpResponse(status=200)
    return HttpResponse(status=400)