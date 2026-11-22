import json

from django.contrib import messages as flash
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import MessageForm
from .models import Conversation, Message
from .services import send_message

User = get_user_model()


def _get_conversation(request, pk):
    """Return the conversation only if the current user participates (else 404)."""
    convo = Conversation.objects.for_user(request.user).filter(pk=pk).first()
    if convo is None:
        raise Http404("Conversation not found")
    return convo


def _serialize(msg, user):
    return {
        "id": msg.id, "body": msg.body, "sender": msg.sender.display_name, "mine": msg.sender_id == user.id,
        "time": timezone.localtime(msg.created_at).strftime("%d %b, %I:%M %p"),
    }


@login_required
def inbox(request):
    conversations = []
    for convo in Conversation.objects.for_user(request.user).prefetch_related("participants"):
        last = convo.messages.order_by("-created_at").first()
        conversations.append({
            "obj": convo,
            "other": convo.other_participant(request.user),
            "last": last,
            "unread": convo.messages.filter(is_read=False).exclude(sender=request.user).count(),
        })
    return render(request, "messaging/inbox.html", {"conversations": conversations})


@login_required
def conversation(request, pk):
    convo = _get_conversation(request, pk)
    convo.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    msgs = convo.messages.select_related("sender")
    return render(request, "messaging/conversation.html", {
        "conversation": convo, "other": convo.other_participant(request.user), "chat_messages": msgs,
        "form": MessageForm(), "last_id": msgs.last().id if msgs.exists() else 0,
    })


@login_required
def start_conversation(request, user_id):
    other = get_object_or_404(User, pk=user_id, is_active=True)
    if other == request.user:
        flash.info(request, "You can't message yourself.")
        return redirect("messaging:inbox")
    subject = request.GET.get("subject", "")[:150]
    convo, _ = Conversation.get_or_create_between(request.user, other, subject=subject)
    return redirect("messaging:conversation", pk=convo.pk)


@login_required
@require_GET
def api_messages(request, pk):
    convo = _get_conversation(request, pk)
    try:
        after = int(request.GET.get("after", 0))
    except ValueError:
        after = 0
    new = convo.messages.filter(id__gt=after).select_related("sender")
    new.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    return JsonResponse({"messages": [_serialize(m, request.user) for m in new]})


@login_required
@require_POST
def api_send(request, pk):
    convo = _get_conversation(request, pk)
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)
    else:
        data = request.POST
    form = MessageForm(data)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    other = convo.other_participant(request.user)
    msg = send_message(request.user, other, form.cleaned_data["body"])
    return JsonResponse({"ok": True, "message": _serialize(msg, request.user)})


@login_required
@require_POST
def send_fallback(request, pk):
    """Non-JS fallback for sending a message."""
    convo = _get_conversation(request, pk)
    form = MessageForm(request.POST)
    if form.is_valid():
        send_message(request.user, convo.other_participant(request.user), form.cleaned_data["body"])
    return redirect("messaging:conversation", pk=pk)


@login_required
@require_GET
def api_unread_count(request):
    count = Message.objects.filter(conversation__participants=request.user, is_read=False).exclude(
        sender=request.user).count()
    return JsonResponse({"unread": count})
