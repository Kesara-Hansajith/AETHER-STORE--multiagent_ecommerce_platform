from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.conf import settings
from .models import Feedback
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, XSD
from django.core.paginator import Paginator
import uuid
import os
from datetime import datetime

class BaseOntologyView(View):
    """Base view for handling RDF graph operations"""
    def __init__(self):
        super().__init__()
        self.graph = Graph()
        self.ontology_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                         'ontology', 'Ecommerce_Platform.xml')
        try:
            self.graph.parse(self.ontology_path)
        except Exception as e:
            print(f"Error loading ontology: {e}")
            # Initialize empty graph if file doesn't exist
            pass
        self.ECOM_NS = Namespace("http://www.example.org/ecommerce_ontology#")
    
    def save_graph(self):
        """Safely save the RDF graph to file"""
        try:
            self.graph.serialize(destination=self.ontology_path, format="xml")
        except Exception as e:
            print(f"Error saving ontology: {e}")
            raise

class LoginView(View):
    """Handle user and admin authentication"""
    def get(self, request):
        # Clear any existing session and logout
        logout(request)
        request.session.flush()
        
        return render(request, 'store/index.html')
    
    def post(self, request):
        form_type = request.POST.get('form_type', 'user')
        username = request.POST.get(f'{form_type}_name')
        password = request.POST.get(f'{form_type}_password')
        
        # In production, replace with proper authentication
        credentials = {
            'user': {'username': 'JohnDoe', 'password': 'JohnDoe'},
            'admin': {'username': 'Admin', 'password': 'Admin'}
        }
        
        if (username == credentials[form_type]['username'] and 
            password == credentials[form_type]['password']):
            # Clear any existing session first
            request.session.flush()
            
            # Set session data
            request.session['user_type'] = form_type
            request.session['username'] = username
            
            # Handle Django authentication
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(username=username)
            login(request, user)
            
            return redirect('baseUser' if form_type == 'user' else 'baseAdmin')
        
        messages.error(request, f'Invalid {form_type} credentials')
        return render(request, 'store/index.html', {'error': f'Invalid {form_type} credentials'})

class AddFeedbackView(LoginRequiredMixin, View):
    """Handle user feedback submission"""
    def get(self, request):
        if request.session.get('user_type') != 'user':
            raise PermissionDenied
            
        context = {
            'range': range(5),  # For star rating display
        }
        return render(request, 'store/user/add_feedback.html', context)
    
    def post(self, request):
        try:
            # Validate user session
            if request.session.get('user_type') != 'user':
                raise PermissionDenied
                
            # Get form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            rating = request.POST.get('rating')
            feedback_text = request.POST.get('feedback')
            
            # Validate required fields
            if not all([name, email, rating, feedback_text]):
                messages.error(request, 'All fields are required')
                return redirect('add_feedback')
                
            # Validate rating
            try:
                rating = int(rating)
                if not 1 <= rating <= 5:
                    raise ValueError
            except (TypeError, ValueError):
                messages.error(request, 'Invalid rating value')
                return redirect('add_feedback')
                
            # Create feedback
            feedback = Feedback.objects.create(
                user=name,
                rating=rating,
                comment=feedback_text
            )
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('user_product_list')  # Redirect to products page after submission
            
        except Exception as e:
            messages.error(request, f'Error submitting feedback: {str(e)}')
            return redirect('add_feedback')


class FeedbackView(LoginRequiredMixin, BaseOntologyView):
    """View for handling feedback display and management"""
    def get(self, request):
        if request.session.get('user_type') != 'admin':
            raise PermissionDenied
            
        # Get all feedback ordered by creation date
        feedback_list = Feedback.objects.all().order_by('-created_at')
        
        # Paginate the feedback list - 10 items per page
        paginator = Paginator(feedback_list, 10)
        page = request.GET.get('page')
        feedbacks = paginator.get_page(page)
        
        context = {
            'feedbacks': feedbacks,
            'star_range': range(5)
        }
        return render(request, 'store/admin/feedbacks.html', context)
    
    def post(self, request):
        """Handle feedback deletion"""
        if request.session.get('user_type') != 'admin':
            raise PermissionDenied
            
        feedback_id = request.POST.get('feedback_id')
        if not feedback_id:
            messages.error(request, 'Feedback ID is required')
            return redirect('view_feedbacks')
            
        try:
            feedback = get_object_or_404(Feedback, id=feedback_id)
            feedback.delete()
            messages.success(request, 'Feedback deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting feedback: {str(e)}')
            
        return redirect('view_feedbacks')

class UserDashboardView(LoginRequiredMixin, BaseOntologyView):
    """User dashboard view with integrated product display"""
    def get(self, request):
        if request.session.get('user_type') != 'user':
            raise PermissionDenied
        
        # Create instance of ProductView to access product methods
        product_view = UserProductView()
        promotional_products, regular_products = product_view.get_products_by_discount()
        
        context = {
            'username': request.session.get('username'),
            'last_login': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'promotional_products': promotional_products,
            'regular_products': regular_products,
            'MEDIA_URL': settings.MEDIA_URL
        }
        return render(request, 'store/baseUser.html', context)

class AdminDashboardView(LoginRequiredMixin, BaseOntologyView):
    """Admin dashboard view"""
    def get(self, request):
        if request.session.get('user_type') != 'admin':
            raise PermissionDenied
        return render(request, 'store/baseAdmin.html')

class ProductView(BaseOntologyView):
    """Base class for product views"""
    def get_products_by_discount(self):
        promotional_products = []
        regular_products = []
        
        for product in self.graph.subjects(RDF.type, self.ECOM_NS.Product):
            try:
                product_data = {
                    'name': str(self.graph.value(product, self.ECOM_NS.name)),
                    'price': float(self.graph.value(product, self.ECOM_NS.price)),
                    'stock': int(self.graph.value(product, self.ECOM_NS.stockLevel)),
                    'discount': float(self.graph.value(product, self.ECOM_NS.discount, 
                                                     default=Literal(0.0))),
                    'image': str(self.graph.value(product, self.ECOM_NS.hasImage, 
                                                default=Literal("default_image.jpg")))
                }
                product_data['final_price'] = round(
                    product_data['price'] * (1 - product_data['discount']/100), 2
                )
                
                # Separate products based on discount
                if product_data['discount'] > 0:
                    promotional_products.append(product_data)
                else:
                    regular_products.append(product_data)
                    
            except Exception as e:
                print(f"Error processing product {product}: {e}")
                continue
                
        return promotional_products, regular_products

class UserProductView(LoginRequiredMixin, ProductView):
    """User product listing view"""
    def get(self, request):
        if request.session.get('user_type') != 'user':
            raise PermissionDenied
            
        promotional_products, regular_products = self.get_products_by_discount()
        
        return render(request, 'store/user/userproducts.html', {
            'promotional_products': promotional_products,
            'regular_products': regular_products,
            'MEDIA_URL': settings.MEDIA_URL
        })

class AdminProductView(LoginRequiredMixin, ProductView):
    """Admin product management view"""
    def get_all_products(self):
        """Retrieve all products from the RDF graph with their details"""
        products = []
        for product in self.graph.subjects(RDF.type, self.ECOM_NS.Product):
            try:
                product_data = {
                    'name': str(self.graph.value(product, self.ECOM_NS.name)),
                    'price': float(self.graph.value(product, self.ECOM_NS.price)),
                    'stock': int(self.graph.value(product, self.ECOM_NS.stockLevel)),
                    'discount': float(self.graph.value(product, self.ECOM_NS.discount, default=Literal(0.0))),
                    'image': str(self.graph.value(product, self.ECOM_NS.hasImage, default=Literal("default_image.jpg")))
                }
                # Calculate final price if there's a discount
                if product_data['discount'] > 0:
                    product_data['final_price'] = round(
                        product_data['price'] * (1 - product_data['discount']/100), 2
                    )
                products.append(product_data)
            except Exception as e:
                print(f"Error processing product {product}: {e}")
                continue
        return products

    def get(self, request, product_id=None):
        if request.session.get('user_type') != 'admin':
            raise PermissionDenied
        
        if product_id:
            # Find the specific product for updating
            product = None
            for p in self.graph.subjects(RDF.type, self.ECOM_NS.Product):
                if str(p).split('#')[-1] == product_id:
                    product = {
                        'id': product_id,
                        'name': str(self.graph.value(p, self.ECOM_NS.name)),
                        'price': float(self.graph.value(p, self.ECOM_NS.price)),
                        'stock': int(self.graph.value(p, self.ECOM_NS.stockLevel)),
                        'discount': float(self.graph.value(p, self.ECOM_NS.discount, default=Literal(0.0))),
                        'image': str(self.graph.value(p, self.ECOM_NS.hasImage, default=Literal("default_image.jpg")))
                    }
                    break
            
            if not product:
                messages.error(request, 'Product not found')
                return redirect('admin_product_list')
                
            return render(request, 'store/admin/update_product.html', {'product': product})
        
        return render(request, 'store/admin/adminproducts.html', {
            'adminproducts': self.get_all_products(),
            'MEDIA_URL': settings.MEDIA_URL
        })

    def post(self, request, product_id=None):
        if request.session.get('user_type') != 'admin':
            raise PermissionDenied

        action = request.POST.get('action')
        
        try:
            # Find the product in the graph
            product = None
            for p in self.graph.subjects(RDF.type, self.ECOM_NS.Product):
                if str(p).split('#')[-1] == product_id:
                    product = p
                    break
            
            if not product:
                messages.error(request, 'Product not found')
                return redirect('admin_product_list')

            if action == 'delete':
                # Remove all triples about this product
                for p, o in self.graph.predicate_objects(product):
                    self.graph.remove((product, p, o))
                messages.success(request, 'Product deleted successfully')
                
            elif action == 'update':
                # Update product properties
                updates = [
                    (self.ECOM_NS.price, Literal(float(request.POST.get('price', 0)), datatype=XSD.float)),
                    (self.ECOM_NS.stockLevel, Literal(int(request.POST.get('stock_level', 0)), datatype=XSD.integer)),
                    (self.ECOM_NS.discount, Literal(float(request.POST.get('discount', 0)), datatype=XSD.float))
                ]

                # Handle image update if provided
                if request.FILES.get('image'):
                    image = request.FILES['image']
                    image_path = os.path.join('product_images', image.name)
                    os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, image_path)), exist_ok=True)
                    
                    with open(os.path.join(settings.MEDIA_ROOT, image_path), 'wb+') as f:
                        for chunk in image.chunks():
                            f.write(chunk)
                            
                    updates.append((self.ECOM_NS.hasImage, Literal(image_path, datatype=XSD.string)))

                # Update the graph
                for predicate, new_value in updates:
                    # Remove old value if it exists
                    old_value = self.graph.value(product, predicate)
                    if old_value:
                        self.graph.remove((product, predicate, old_value))
                    # Add new value
                    self.graph.add((product, predicate, new_value))

                messages.success(request, 'Product updated successfully')

            self.save_graph()
            return redirect('admin_product_list')
            
        except Exception as e:
            messages.error(request, f'Error processing product: {str(e)}')
            return redirect('admin_product_list')

class OrderView(LoginRequiredMixin, BaseOntologyView):
    """Handle order creation and management"""
    def get(self, request):
        if request.session.get('user_type') != 'user':
            raise PermissionDenied
            
        # Get both promotional and regular products
        user_product_view = UserProductView()
        promotional_products, regular_products = user_product_view.get_products_by_discount()
        
        # Combine all products for the order form
        all_products = promotional_products + regular_products
        
        return render(request, 'store/user/order_form.html', {
            'products': all_products,
            'MEDIA_URL': settings.MEDIA_URL
        })
    
    def post(self, request):
        try:
            product_name = request.POST.get('product_name')
            quantity = int(request.POST.get('quantity', 0))
            
            # Validate input
            if quantity <= 0:
                messages.error(request, 'Quantity must be greater than 0')
                return redirect('order')
            
            # Find product
            product = next(
                (p for p in self.graph.subjects(self.ECOM_NS.name, 
                Literal(product_name, datatype=XSD.string))), None
            )
            
            if not product:
                messages.error(request, 'Product not found')
                return redirect('order')
            
            # Check stock
            stock = int(self.graph.value(product, self.ECOM_NS.stockLevel))
            if stock < quantity:
                messages.error(request, f'Insufficient stock. Only {stock} available')
                return redirect('order')
            
            # Get product price and discount
            price = float(self.graph.value(product, self.ECOM_NS.price))
            discount = float(self.graph.value(product, self.ECOM_NS.discount, 
                                            default=Literal(0.0)))
            
            # Calculate final price
            final_price = price * (1 - discount/100)
            
            # Create order
            order_id = str(uuid.uuid4())
            order = URIRef(self.ECOM_NS + order_id)
            
            # Add order details
            order_data = [
                (RDF.type, self.ECOM_NS.Order),
                (self.ECOM_NS.customer, Literal(request.session.get('username', 'Unknown'), 
                                              datatype=XSD.string)),
                (self.ECOM_NS.product, product),
                (self.ECOM_NS.quantity, Literal(quantity, datatype=XSD.integer)),
                (self.ECOM_NS.price, Literal(final_price, datatype=XSD.float)),
                (self.ECOM_NS.status, Literal("pending", datatype=XSD.string)),
                (self.ECOM_NS.orderDate, Literal(datetime.now().isoformat(), 
                                               datatype=XSD.dateTime))
            ]
            
            for predicate, obj in order_data:
                self.graph.add((order, predicate, obj))
            
            # Update stock
            self.graph.set((product, self.ECOM_NS.stockLevel, Literal(stock - quantity)))
            
            self.save_graph()
            messages.success(request, 'Order placed successfully!')
            return redirect('order_success')
            
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return redirect('order')

class ViewOrdersView(LoginRequiredMixin, BaseOntologyView):
    """View and manage orders"""
    def get(self, request):
        if request.session.get('user_type') != 'admin':
            raise PermissionDenied
            
        orders = []
        for order in self.graph.subjects(RDF.type, self.ECOM_NS.Order):
            try:
                order_data = {
                    'id': str(order).split('#')[-1],
                    'customer': str(self.graph.value(order, self.ECOM_NS.customer) or "Unknown"),
                    'product': str(self.graph.value(self.graph.value(order, self.ECOM_NS.product), 
                                                  self.ECOM_NS.name) or "Unknown Product"),
                    'quantity': int(self.graph.value(order, self.ECOM_NS.quantity) or 0),
                    'status': str(self.graph.value(order, self.ECOM_NS.status) or "unknown"),
                    'date': self.graph.value(order, self.ECOM_NS.orderDate)
                }
                orders.append(order_data)
            except Exception as e:
                print(f"Error processing order {order}: {str(e)}")
                continue
            
        return render(request, 'store/admin/orders.html', {'orders': orders})

class AdminView(LoginRequiredMixin, BaseOntologyView):
    """Admin dashboard and product management"""
    def get(self, request):
        if request.session.get('user_type') != 'admin':
            raise PermissionDenied
            
        products = AdminProductView().get_all_products()
        return render(request, 'store/admin/dashboard.html', {'products': products})

    def post(self, request):
        try:
            # Validate input
            product_name = request.POST.get('name')
            if not product_name:
                messages.error(request, 'Product name is required')
                return redirect('baseAdmin')
                
            # Process product data
            product_data = {
                'price': float(request.POST.get('price', 0)),
                'stock_level': int(request.POST.get('stock_level', 0)),
                'discount': float(request.POST.get('discount', 0)),
            }
            
            # Handle image upload
            image = request.FILES.get('image')
            if image:
                image_path = os.path.join('product_images', image.name)
                os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, image_path)), 
                           exist_ok=True)
                with open(os.path.join(settings.MEDIA_ROOT, image_path), 'wb+') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
            else:
                image_path = 'default_image.jpg'

            # Create product in RDF graph
            product_id = product_name.lower().replace(" ", "_")
            product = URIRef(self.ECOM_NS + product_id)

            # Add product properties
            product_properties = [
                (RDF.type, self.ECOM_NS.Product),
                (self.ECOM_NS.name, Literal(product_name, datatype=XSD.string)),
                (self.ECOM_NS.price, Literal(product_data['price'], datatype=XSD.float)),
                (self.ECOM_NS.stockLevel, Literal(product_data['stock_level'], 
                                                datatype=XSD.integer)),
                (self.ECOM_NS.discount, Literal(product_data['discount'], datatype=XSD.float)),
                (self.ECOM_NS.hasImage, Literal(image_path, datatype=XSD.string))
            ]

            for predicate, obj in product_properties:
                self.graph.add((product, predicate, obj))

            self.save_graph()
            messages.success(request, 'Product added successfully!')
            return redirect('baseAdmin')
            
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
            return redirect('baseAdmin')
