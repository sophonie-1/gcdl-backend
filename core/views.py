from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from functools import wraps
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from reportlab.pdfgen import canvas
from io import BytesIO
from .forms import RegisterForm, ProcurementForm, SaleForm, CreditSaleForm
from .models import Produce, Procurement, Sale, CreditSale, Stock

def agent_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.groups.filter(name='Agent').exists():
            return JsonResponse({'error': 'Agent access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def manager_ceo_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.groups.filter(name__in=['Manager', 'CEO']).exists() == False:
            return JsonResponse({'error': 'Manager or CEO access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Auth Views (Step 2)
class RegisterView(View):
    @method_decorator(csrf_exempt)
    def post(self, request):
        data = json.loads(request.body)
        form = RegisterForm(data)
        if form.is_valid():
            user = form.save()
            return JsonResponse({'success': True, 'role': user.groups.first().name if user.groups.exists() else 'Agent'})
        return JsonResponse({'error': form.errors}, status=400)

class LoginView(View):
    @method_decorator(csrf_exempt)
    def post(self, request):
        data = json.loads(request.body)
        user = authenticate(request, username=data.get('username'), password=data.get('password'))
        if user:
            login(request, user)
            role = user.groups.first().name if user.groups.exists() else 'None'
            return JsonResponse({'success': True, 'role': role, 'user_id': user.id})
        return JsonResponse({'error': 'Invalid credentials'}, status=400)

class LogoutView(View):
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def post(self, request):
        logout(request)
        return JsonResponse({'success': True})

# Produce List (for dropdowns)
class ProduceListView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def get(self, request):
        produces = Produce.objects.values('id', 'name', 'type', 'branch')
        return JsonResponse(list(produces), safe=False)

# Procurement Views
class ProcurementListView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def get(self, request):
        procurements = Procurement.objects.select_related('produce').all().values(
            'id', 'produce__name', 'produce__type', 'tonnage', 'cost', 'dealer_name', 
            'dealer_contact', 'branch', 'selling_price', 'date_time'
        )
        return JsonResponse(list(procurements), safe=False)

class ProcurementCreateView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(agent_required)
    def post(self, request):
        data = json.loads(request.body)
        form = ProcurementForm(data)
        if form.is_valid():
            procurement = form.save()
            return JsonResponse({'success': True, 'id': procurement.id})
        return JsonResponse({'error': form.errors}, status=400)

class ProcurementUpdateView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(agent_required)
    def post(self, request, pk):
        try:
            procurement = Procurement.objects.get(pk=pk)
        except Procurement.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
        data = json.loads(request.body)
        form = ProcurementForm(data, instance=procurement)
        old_tonnage = procurement.tonnage
        if form.is_valid():
            form.save()
            stock = Stock.objects.get(produce=procurement.produce)
            delta = procurement.tonnage - old_tonnage
            stock.current_tonnage += delta
            stock.save()
            return JsonResponse({'success': True})
        return JsonResponse({'error': form.errors}, status=400)

class ProcurementDeleteView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(agent_required)
    def post(self, request, pk):
        try:
            procurement = Procurement.objects.get(pk=pk)
            stock = Stock.objects.get(produce=procurement.produce)
            stock.current_tonnage -= procurement.tonnage
            stock.save()
            procurement.delete()
            return JsonResponse({'success': True})
        except (Procurement.DoesNotExist, Stock.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)

# Sales Views
class SaleListView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def get(self, request):
        sales = Sale.objects.select_related('produce', 'agent').all().values(
            'id', 'produce__name', 'produce__type', 'tonnage', 'amount_paid', 'buyer_name',
            'buyer_contact', 'agent__username', 'date_time', 'is_credit', 'receipt_id'
        )
        return JsonResponse(list(sales), safe=False)

class SaleCreateView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(agent_required)
    def post(self, request):
        data = json.loads(request.body)
        form = SaleForm(data)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.agent = request.user
            sale.save()  # Triggers signal

            if data.get('is_credit'):
                credit_data = {k: data[k] for k in ['national_id', 'location', 'amount_due', 'due_date']}
                credit_form = CreditSaleForm(credit_data)
                if credit_form.is_valid():
                    credit = credit_form.save(commit=False)
                    credit.sale = sale
                    credit.save()
                else:
                    sale.delete()
                    return JsonResponse({'error': credit_form.errors}, status=400)

            return JsonResponse({'success': True, 'receipt_id': sale.receipt_id})
        return JsonResponse({'error': form.errors}, status=400)

class SaleUpdateView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(agent_required)
    def post(self, request, pk):
        # Similar to ProcurementUpdate; stock delta
        return JsonResponse({'error': 'Update TBD'}, status=501)

class SaleDeleteView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(agent_required)
    def post(self, request, pk):
        try:
            sale = Sale.objects.get(pk=pk)
            stock = Stock.objects.get(produce=sale.produce)
            stock.current_tonnage += sale.tonnage
            stock.save()
            sale.delete()
            return JsonResponse({'success': True})
        except Sale.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)

class ReceiptDownloadView(LoginRequiredMixin, View):
    def get(self, request, receipt_id):
        try:
            sale = Sale.objects.get(receipt_id=receipt_id)
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            y = 750
            p.drawString(100, y, f"GCDL Receipt {sale.receipt_id}"); y -= 20
            p.drawString(100, y, f"Buyer: {sale.buyer_name}"); y -= 20
            p.drawString(100, y, f"Produce: {sale.produce.name} - {sale.tonnage}t"); y -= 20
            p.drawString(100, y, f"Amount: {sale.amount_paid}"); y -= 20
            p.drawString(100, y, f"Date: {sale.date_time}"); y -= 20
            if sale.is_credit:
                credit = CreditSale.objects.get(sale=sale)
                p.drawString(100, y, f"Due: {credit.due_date} - {credit.amount_due}"); y -= 20
            p.save()
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{receipt_id}.pdf"'
            return response
        except Sale.DoesNotExist:
            return JsonResponse({'error': 'Receipt not found'}, status=404)

# Stock View
class StockListView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def get(self, request):
        stocks = Stock.objects.select_related('produce').all().values(
            'produce__name', 'produce__type', 'current_tonnage'
        )
        return JsonResponse(list(stocks), safe=False)

class StockUpdateView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(manager_ceo_required)
    def post(self, request, pk):
        data = json.loads(request.body)
        try:
            stock = Stock.objects.get(pk=pk)
            stock.current_tonnage = data['current_tonnage']
            stock.save()
            return JsonResponse({'success': True})
        except Stock.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)

# Basic Analytics (KPIs, trends, reports)
class AnalyticsKPIsView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(manager_ceo_required)
    def get(self, request):
        total_sales = Sale.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        total_procurements = Procurement.objects.aggregate(Sum('cost'))['cost__sum'] or 0
        profit_margin = ((total_sales - total_procurements) / total_sales * 100) if total_sales > 0 else 0
        stock_turnover = Sale.objects.aggregate(Sum('tonnage'))['tonnage__sum'] or 0
        top_dealer = Procurement.objects.values('dealer_name').annotate(total=Sum('tonnage')).order_by('-total')[:5]
        return JsonResponse({
            'total_sales': total_sales,
            'profit_margin': round(profit_margin, 2),
            'stock_turnover': stock_turnover,
            'top_dealers': list(top_dealer)
        })

class AnalyticsTrendsView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    @method_decorator(manager_ceo_required)
    def get(self, request):
        trends = Sale.objects.annotate(month=TruncMonth('date_time')).values('month').annotate(total=Sum('amount_paid'))
        return JsonResponse(list(trends), safe=False)