from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from messaging.services import send_message
from notifications.models import Notification
from notifications.utils import notify

from .forms import EnquiryForm, ProductFilterForm, ProductForm, ReportForm
from .models import Enquiry, Product, ProductReport, SavedProduct

User = get_user_model()

SORT_MAP = {"newest": "-created_at", "oldest": "created_at", "price_asc": "price", "price_desc": "-price"}


def filter_products(params):
    qs = Product.objects.filter(is_hidden=False).select_related("seller")
    form = ProductFilterForm(params)
    order = "-created_at"
    if form.is_valid():
        d = form.cleaned_data
        if d["q"]:
            qs = qs.filter(Q(title__icontains=d["q"]) | Q(description__icontains=d["q"]))
        if d["category"]:
            qs = qs.filter(category=d["category"])
        if d["condition"]:
            qs = qs.filter(condition=d["condition"])
        if d["min_price"] is not None:
            qs = qs.filter(price__gte=d["min_price"])
        if d["max_price"] is not None:
            qs = qs.filter(price__lte=d["max_price"])
        if not d["include_sold"]:
            qs = qs.exclude(status=Product.Status.SOLD)
        order = SORT_MAP.get(d["sort"] or "newest", "-created_at")
    else:
        qs = qs.exclude(status=Product.Status.SOLD)
    return qs.order_by(order), form


def _saved_ids(user):
    return set(SavedProduct.objects.filter(user=user).values_list("product_id", flat=True))


def _get_own_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.seller != request.user and not request.user.is_site_admin:
        raise PermissionDenied("You can only manage your own listings.")
    return product


@login_required
def product_list(request):
    qs, form = filter_products(request.GET)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    return render(request, "marketplace/list.html", {
        "page_obj": page, "filter_form": form, "saved_ids": _saved_ids(request.user)})


@login_required
@require_GET
def api_search(request):
    qs, _ = filter_products(request.GET)
    qs = list(qs[:36])
    saved = _saved_ids(request.user)
    html = render_to_string("marketplace/_cards.html", {"products": qs, "saved_ids": saved}, request=request)
    results = [{"id": p.id, "title": p.title, "price": str(p.price), "category": p.get_category_display(),
                "condition": p.get_condition_display(), "status": p.status, "saved": p.id in saved,
                "url": p.get_absolute_url()} for p in qs]
    return JsonResponse({"count": len(results), "results": results, "html": html})


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("seller", "seller__profile"), pk=pk)
    if product.is_hidden and product.seller != request.user and not request.user.is_site_admin:
        raise PermissionDenied("This listing has been hidden by moderators.")
    is_owner = product.seller == request.user
    context = {
        "product": product, "is_owner": is_owner,
        "is_saved": SavedProduct.objects.filter(user=request.user, product=product).exists(),
        "enquiry_form": EnquiryForm(), "report_form": ReportForm(),
        "enquiries": product.enquiries.select_related("buyer") if is_owner else None,
        "similar": Product.objects.filter(category=product.category, is_hidden=False,
                                          status=Product.Status.AVAILABLE).exclude(pk=product.pk)[:4],
    }
    return render(request, "marketplace/detail.html", context)


@login_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        messages.success(request, "Your product is live on the marketplace.")
        return redirect(product)
    return render(request, "marketplace/form.html", {"form": form, "title": "Sell an item"})


@login_required
def product_edit(request, pk):
    product = _get_own_product(request, pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Listing updated.")
        return redirect(product)
    return render(request, "marketplace/form.html", {"form": form, "title": "Edit listing", "product": product})


@login_required
def product_delete(request, pk):
    product = _get_own_product(request, pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Listing deleted.")
        return redirect("marketplace:my_listings")
    return render(request, "confirm_delete.html", {"object": product, "cancel_url": product.get_absolute_url()})


@login_required
@require_POST
def api_toggle_save(request, pk):
    product = get_object_or_404(Product, pk=pk, is_hidden=False)
    saved = SavedProduct.objects.filter(user=request.user, product=product)
    if saved.exists():
        saved.delete()
        is_saved = False
    else:
        SavedProduct.objects.create(user=request.user, product=product)
        is_saved = True
    return JsonResponse({"ok": True, "saved": is_saved, "count": product.savedproduct_set.count()})


@login_required
@require_POST
def api_update_status(request, pk):
    product = _get_own_product(request, pk)
    status = request.POST.get("status")
    if status not in Product.Status.values:
        return JsonResponse({"ok": False, "error": "Invalid status"}, status=400)
    product.status = status
    product.sold_at = timezone.now() if status == Product.Status.SOLD else None
    product.save(update_fields=["status", "sold_at", "updated_at"])
    return JsonResponse({"ok": True, "status": product.status, "label": product.get_status_display()})


@login_required
@require_POST
def enquire(request, pk):
    product = get_object_or_404(Product, pk=pk, is_hidden=False)
    if product.seller == request.user:
        messages.info(request, "This is your own listing.")
        return redirect(product)
    form = EnquiryForm(request.POST)
    if form.is_valid():
        enquiry = form.save(commit=False)
        enquiry.product, enquiry.buyer = product, request.user
        enquiry.save()
        offer = f" Offer: ₹{enquiry.offered_price}." if enquiry.offered_price else ""
        msg = send_message(request.user, product.seller, f"[Enquiry: {product.title}] {enquiry.message}{offer}",
                           subject=product.title)
        notify(product.seller, Notification.Type.ENQUIRY, f"New enquiry on '{product.title}'",
               f"{request.user.display_name}: {enquiry.message}", reverse("marketplace:detail", args=[product.pk]),
               request.user)
        messages.success(request, "Enquiry sent! Continue the chat in Messages.")
        return redirect("messaging:conversation", pk=msg.conversation_id)
    messages.error(request, "Please write a message for the seller.")
    return redirect(product)


@login_required
@require_POST
def report(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ReportForm(request.POST)
    if ProductReport.objects.filter(product=product, reporter=request.user).exists():
        messages.info(request, "You've already reported this listing.")
    elif form.is_valid():
        try:
            with transaction.atomic():
                rep = form.save(commit=False)
                rep.product, rep.reporter = product, request.user
                rep.save()
            messages.success(request, "Thanks — our moderators will review this listing.")
        except IntegrityError:  # concurrent duplicate
            messages.info(request, "You've already reported this listing.")
    else:
        messages.error(request, "Please choose a reason.")
    return redirect(product)


@login_required
def my_listings(request):
    products = Product.objects.filter(seller=request.user)
    enquiries = Enquiry.objects.filter(product__seller=request.user).select_related("buyer", "product")[:20]
    return render(request, "marketplace/my_listings.html", {"products": products, "enquiries": enquiries})


@login_required
def saved_products(request):
    products = request.user.saved_products.filter(is_hidden=False)
    return render(request, "marketplace/saved.html", {"products": products, "saved_ids": {p.id for p in products}})


@login_required
def seller_profile(request, username):
    seller = get_object_or_404(User.objects.select_related("profile"), username=username, is_active=True)
    products = Product.objects.filter(seller=seller, is_hidden=False)
    return render(request, "marketplace/seller.html", {
        "seller": seller, "products": products, "saved_ids": _saved_ids(request.user),
        "sold_count": products.filter(status=Product.Status.SOLD).count()})
