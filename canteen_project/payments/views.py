from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from orders.models import Order
from accounts.models import UserProfile
from .models import Payment, WalletTransaction
import uuid
import stripe
import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

# Wallet configuration
MAX_WALLET_BALANCE = 10000  # Maximum wallet balance allowed
MAX_SINGLE_TOPUP = 5000     # Maximum single topup amount
MIN_TOPUP_AMOUNT = 10       # Minimum topup amount


def _get_client_ip(request):
    """Extract real client IP address, respecting reverse proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def payment_page(request, order_id):
    """Show payment options"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.is_paid:
        messages.info(request, 'Order already paid')
        return redirect('order_history')

    wallet_balance = request.user.profile.wallet_balance
    wallet_sufficient = wallet_balance >= order.total_amount
    wallet_shortfall = max(order.total_amount - wallet_balance, 0)

    context = {
        'order': order,
        'wallet_balance': wallet_balance,
        'wallet_sufficient': wallet_sufficient,
        'wallet_shortfall': wallet_shortfall,
    }
    return render(request, 'payments/payment_page.html', context)


@login_required
@transaction.atomic
def process_cash_payment(request, order_id):
    """Process cash payment"""
    if request.method != 'POST':
        return redirect('payment_page', order_id=order_id)

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.is_paid:
        messages.info(request, 'Order already paid')
        return redirect('order_history')

    Payment.objects.create(
        order=order,
        amount=order.total_amount,
        method='cash',
        status='pending',
        ip_address=_get_client_ip(request),
    )

    order.transition_to('pending')
    order.save()

    messages.success(request, 'Order confirmed! Pay at counter.')
    return redirect('order_history')


@login_required
@transaction.atomic
def process_wallet_payment(request, order_id):
    """Process wallet payment with atomic transaction to prevent race conditions"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Lock the profile row to prevent concurrent modifications
    profile = UserProfile.objects.select_for_update().get(user=request.user)

    if profile.wallet_balance < order.total_amount:
        messages.error(request, 'Insufficient wallet balance')
        return redirect('payment_page', order_id=order_id)

    # Deduct from wallet (now atomic)
    profile.wallet_balance -= order.total_amount
    profile.save()

    txn_ref = str(uuid.uuid4()).replace('-', '').upper()[:12]

    # Record transaction
    WalletTransaction.objects.create(
        user=request.user,
        amount=order.total_amount,
        transaction_type='debit',
        description=f'Payment for order #{order.token_number}',
        reference_id=txn_ref,
    )

    # Create payment record
    Payment.objects.create(
        order=order,
        amount=order.total_amount,
        method='wallet',
        status='completed',
        transaction_id=txn_ref,
        ip_address=_get_client_ip(request),
        gateway_response={'source': 'canteen_wallet', 'ref': txn_ref},
    )

    order.is_paid = True
    order.transition_to('confirmed')
    order.save()

    messages.success(request, '✓ Payment successful!')
    return redirect('order_history')


@login_required
def wallet_view(request):
    """Show wallet balance, monthly summary, and paginated transactions"""
    all_txns = WalletTransaction.objects.filter(user=request.user)

    # Monthly summary
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_txns = all_txns.filter(created_at__gte=month_start)
    month_credits = month_txns.filter(transaction_type='credit').aggregate(
        total=Sum('amount'))['total'] or 0
    month_debits = month_txns.filter(transaction_type='debit').aggregate(
        total=Sum('amount'))['total'] or 0

    # Filter
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'credit':
        transactions_list = all_txns.filter(transaction_type='credit')
    elif filter_type == 'debit':
        transactions_list = all_txns.filter(transaction_type='debit')
    else:
        transactions_list = all_txns

    paginator = Paginator(transactions_list, 15)
    page = request.GET.get('page')
    try:
        transactions = paginator.page(page)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)

    balance = request.user.profile.wallet_balance
    cap_pct = min(int((balance / MAX_WALLET_BALANCE) * 100), 100)

    context = {
        'balance': balance,
        'transactions': transactions,
        'month_credits': month_credits,
        'month_debits': month_debits,
        'filter_type': filter_type,
        'max_wallet': MAX_WALLET_BALANCE,
        'cap_pct': cap_pct,
    }
    return render(request, 'payments/wallet.html', context)


@login_required
@transaction.atomic
def add_money_to_wallet(request):
    """Add money to wallet (simulated) with validation"""
    if request.method == 'POST':
        try:
            amount = int(request.POST.get('amount', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount')
            return redirect('wallet')

        # Validate amount limits
        if amount < MIN_TOPUP_AMOUNT:
            messages.error(request, f'Minimum topup amount is ₹{MIN_TOPUP_AMOUNT}')
            return redirect('wallet')

        if amount > MAX_SINGLE_TOPUP:
            messages.error(request, f'Maximum single topup is ₹{MAX_SINGLE_TOPUP}')
            return redirect('wallet')

        # Lock profile to prevent race conditions
        profile = UserProfile.objects.select_for_update().get(user=request.user)

        # Check wallet balance limit
        if profile.wallet_balance + amount > MAX_WALLET_BALANCE:
            messages.error(request, f'Wallet balance cannot exceed ₹{MAX_WALLET_BALANCE}')
            return redirect('wallet')

        profile.wallet_balance += amount
        profile.save()

        ref = str(uuid.uuid4()).replace('-', '').upper()[:12]
        WalletTransaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_type='credit',
            description='Wallet top-up',
            reference_id=ref,
        )

        messages.success(request, f'₹{amount} added to wallet!')

    return redirect('wallet')


@login_required
def process_online_payment(request, order_id):
    """Create a Stripe Checkout Session and redirect the user to Stripe."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if order.is_paid:
        if is_ajax:
            return JsonResponse({'error': 'Order already paid'}, status=400)
        messages.info(request, 'Order already paid')
        return redirect('order_history')

    # Build line items from order items
    line_items = []
    for item in order.items.all():
        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': item.item_name,
                },
                'unit_amount': int(item.price * 100),  # Stripe uses paise
            },
            'quantity': item.quantity,
        })

    # Add delivery fee as a line item if present
    if order.delivery_fee and order.delivery_fee > 0:
        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': f'Delivery Fee ({order.get_delivery_type_display()})',
                },
                'unit_amount': int(order.delivery_fee * 100),
            },
            'quantity': 1,
        })

    try:
        # Build absolute URLs for success/cancel
        success_url = request.build_absolute_uri(f'/payment/{order.id}/stripe/success/') + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.build_absolute_uri(f'/payment/{order.id}/')

        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.user.email or None,
            metadata={
                'order_id': str(order.id),
                'user_id': str(request.user.id),
                'token_number': str(order.token_number),
            },
        )

        if is_ajax:
            return JsonResponse({'url': checkout_session.url})
        response = redirect(checkout_session.url)
        response.status_code = 303
        return response

    except stripe.error.StripeError as e:
        logger.error(f'Stripe error creating session for order {order.id}: {e}')
        if is_ajax:
            return JsonResponse({'error': 'Unable to connect to payment gateway. Please try again.'}, status=502)
        messages.error(request, 'Unable to connect to payment gateway. Please try again.')
        return redirect('payment_page', order_id=order_id)


@login_required
@transaction.atomic
def stripe_success(request, order_id):
    """Handle return from Stripe after successful payment."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.is_paid:
        messages.info(request, 'Order already paid')
        return redirect('order_history')

    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid payment session')
        return redirect('payment_page', order_id=order_id)

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            # Create payment record (idempotent atomic check)
            payment, created = Payment.objects.get_or_create(
                stripe_session_id=session.id,
                defaults={
                    'order': order,
                    'amount': order.total_amount,
                    'method': 'stripe',
                    'status': 'completed',
                    'transaction_id': session.payment_intent or session.id,
                    'ip_address': _get_client_ip(request),
                    'gateway_response': {
                        'gateway': 'stripe',
                        'session_id': session.id,
                        'payment_intent': session.payment_intent,
                        'payment_status': session.payment_status,
                    }
                }
            )

            order.is_paid = True
            order.transition_to('confirmed')
            order.save()

            messages.success(request, f'✓ Payment successful! Transaction ID: {session.payment_intent or session.id}')
            return redirect('order_history')
        else:
            messages.warning(request, 'Payment not yet confirmed. Please try again.')
            return redirect('payment_page', order_id=order_id)

    except stripe.error.StripeError as e:
        logger.error(f'Stripe error verifying session {session_id}: {e}')
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('payment_page', order_id=order_id)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events for reliable payment confirmation."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    # If no webhook secret configured, skip signature verification (dev mode)
    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            logger.warning('Stripe webhook: invalid payload')
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.warning('Stripe webhook: invalid signature')
            return HttpResponse(status=400)
    else:
        import json
        try:
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        except (ValueError, json.JSONDecodeError):
            return HttpResponse(status=400)

    # Handle checkout.session.completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('metadata', {}).get('order_id')

        if order_id:
            try:
                with transaction.atomic():
                    order = Order.objects.select_for_update().get(id=int(order_id))

                    # Idempotent — skip if already paid
                    payment, created = Payment.objects.get_or_create(
                        stripe_session_id=session['id'],
                        defaults={
                            'order': order,
                            'amount': order.total_amount,
                            'method': 'stripe',
                            'status': 'completed',
                            'transaction_id': session.get('payment_intent', session['id']),
                            'gateway_response': {
                                'gateway': 'stripe_webhook',
                                'session_id': session['id'],
                                'payment_intent': session.get('payment_intent'),
                                'event_id': event['id'],
                            }
                        }
                    )
                    
                    if created or not order.is_paid:
                        order.is_paid = True
                        order.transition_to('confirmed')
                        order.save()
                        logger.info(f'Stripe webhook: order {order_id} confirmed via webhook')
            except Order.DoesNotExist:
                logger.warning(f'Stripe webhook: order {order_id} not found')
            except Exception as e:
                logger.error(f'Stripe webhook error for order {order_id}: {e}')
                return HttpResponse(status=500)

    return HttpResponse(status=200)


@login_required
def payment_status_api(request, payment_id):
    """JSON API endpoint for payment status polling"""
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    return JsonResponse({
        'id': payment.id,
        'status': payment.status,
        'method': payment.method,
        'display_method': payment.display_method,
        'transaction_id': payment.transaction_id,
        'amount': str(payment.amount),
        'is_refunded': payment.is_refunded,
        'created_at': payment.created_at.isoformat(),
    })
