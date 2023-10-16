from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from .models import Customer, Order, OrderHasProduct, Status, Product
from .forms import NewOrderForm, NewCustomerForm


class WebappLogin(TemplateView):
    template_name = 'webapp/login.html'


class WebappHome(ListView):
    model = Order
    template_name = 'webapp/home.html'
    context_object_name = "commandes"


class CreateOrder(CreateView):
    form_class = NewOrderForm
    template_name = 'webapp/create.html'
    success_url = '/dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'customer_form' not in context:
            context['customer_form'] = NewCustomerForm(self.request.POST or None)
        return context

    def form_valid(self, form):
        customer_form = NewCustomerForm(self.request.POST)
        if customer_form.is_valid():
            # Sauvegarde le Customer, mais ne le commit pas encore en base de données
            customer = customer_form.save(commit=False)
            customer.save()  # Maintenant, le customer est sauvegardé en BDD

            order = form.save(commit=False)  # Récupère l'Order à partir du formulaire sans le sauvegarder en BDD
            order.customer = customer  # Associe le Customer à l'Order
            order.save()  # Sauvegarde maintenant l'Order avec le Customer associé

            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form, customer_form=customer_form))


def simple_customer_view(request):
    if request.method == 'POST':
        form = SimpleCustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('some_success_url')
    else:
        form = SimpleCustomerForm()
    return render(request, 'simple_template.html', {'form': form})


class EditOrder(TemplateView):
    template_name = 'webapp/edit.html'


class DeleteOrder(DeleteView):
    model = Order
    context_object_name = "commandes"
    template_name = 'webapp/delete.html'
    success_url = reverse_lazy("webapp:dashboard")


class Search(TemplateView):
    template_name = 'webapp/search.html'


class DetailOrder(DetailView):
    model = Order
    context_object_name = "commandes"
    template_name = 'webapp/order.html'


class Dashboard(ListView):
    model = Order
    template_name = 'webapp/dashboard.html'
    context_object_name = "commandes"
