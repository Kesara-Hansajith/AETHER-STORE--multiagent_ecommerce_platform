from django.shortcuts import render, redirect
from django.views import View
from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, XSD
from django.contrib import messages
from django.conf import settings
import uuid
import os


class BaseOntologyView(View):
    def __init__(self):
        super().__init__()
        self.graph = Graph()
        # Use os.path to handle file paths properly
        ontology_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ontology', 'Ecommerce_Platform.xml')
        self.graph.parse(ontology_path)
        self.ECOM_NS = Namespace("http://www.example.org/ecommerce_ontology#")
        
    def save_graph(self):
        ontology_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ontology', 'Ecommerce_Platform.xml')
        self.graph.serialize(destination=ontology_path, format="xml")

class LoginView(View):
    def get(self, request):
        """Display login form"""
        return render(request, 'store/index.html')
    
    def post(self, request):
        """Handle login form submission"""        
        form_type = request.POST.get('form_type', 'user')
        
        if form_type == 'user':
            username = request.POST.get('user_name')
            password = request.POST.get('user_password')
            
            print(f"Login attempt - Username: {username}, Password: {password}")
            
            if username == "JohnDoe" and password == "JohnDoe":
                request.session['user_type'] = 'user'
                request.session['username'] = username
                return redirect('baseUser')
            else:
                messages.error(request, 'Invalid user credentials')
                return render(request, 'store/index.html', {'error': 'Invalid user credentials'})
        else:  # admin login
            username = request.POST.get('admin_name')
            password = request.POST.get('admin_password')
            
            if username == "Admin" and password == "Admin":
                request.session['user_type'] = 'admin'
                request.session['username'] = username
                return redirect('baseAdmin')
            else:
                messages.error(request, 'Invalid admin credentials')
                return render(request, 'store/index.html', {'error': 'Invalid admin credentials'})
    
class UserDashboardView(BaseOntologyView):
    def get(self, request):
        """Display user dashboard"""
        if request.session.get('user_type') != 'user':
            return redirect('login')
        return render(request, 'store/baseUser.html')
    
class AdminDashboardView(BaseOntologyView):
    def get(self, request):
        """Display admin dashboard"""
        if request.session.get('user_type') != 'admin':
            return redirect('login')
        return render(request, 'store/baseAdmin.html')

class UserProductView(BaseOntologyView):
    def get(self, request):
        """Display list of products"""
        products = self.get_all_products()
        return render(request, 'store/user/userproducts.html', {
            'userproducts': products,
            'MEDIA_URL': settings.MEDIA_URL
        })
    
    def get_all_products(self):
        products = []
        for product in self.graph.subjects(RDF.type, self.ECOM_NS.Product):
            name = self.graph.value(product, self.ECOM_NS.name)
            price = self.graph.value(product, self.ECOM_NS.price)
            stock = self.graph.value(product, self.ECOM_NS.stockLevel)
            discount = self.graph.value(product, self.ECOM_NS.discount, default=Literal(0.0))
            image = self.graph.value(product, self.ECOM_NS.hasImage, default=Literal("default_image.jpg"))
            
            products.append({
                'name': str(name),
                'price': float(price),
                'stock': int(stock),
                'discount': float(discount),
                'final_price': round(float(price) * (1 - float(discount)/100), 2),
                'image': str(image),  
            })
        return products

class AdminProductView(BaseOntologyView):
    def get(self, request):
        """Display list of products"""
        products = self.get_all_products()
        return render(request, 'store/admin/adminproducts.html', {
            'adminproducts': products,
            'MEDIA_URL': settings.MEDIA_URL  
        })
    
    def get_all_products(self):
        products = []
        for product in self.graph.subjects(RDF.type, self.ECOM_NS.Product):
            name = self.graph.value(product, self.ECOM_NS.name)
            price = self.graph.value(product, self.ECOM_NS.price)
            stock = self.graph.value(product, self.ECOM_NS.stockLevel)
            discount = self.graph.value(product, self.ECOM_NS.discount, default=Literal(0.0))
            image = self.graph.value(product, self.ECOM_NS.hasImage, default=Literal("default_image.jpg"))
            
            products.append({
                'name': str(name),
                'price': float(price),
                'stock': int(stock),
                'discount': float(discount),
                'final_price': round(float(price) * (1 - float(discount)/100), 2),
                'image': str(image),  
            })
        return products

class OrderView(BaseOntologyView):
    def get(self, request):
        """Display order form"""
        # Create a new instance of ProductView to use its methods
        product_view = UserProductView()
        products = product_view.get_all_products()
        return render(request, 'store/user/order_form.html', {'products': products})
    
    def post(self, request):
        """Handle order placement"""
        product_name = request.POST.get('product_name')
        quantity = int(request.POST.get('quantity', 0))
        
        # Find product in RDF graph
        product = next(
            (p for p in self.graph.subjects(self.ECOM_NS.name, 
            Literal(product_name, datatype=XSD.string))), None
        )
        
        if not product:
            return render(request, 'store/error.html', 
                        {'message': 'Product not found'})
        
        stock = int(self.graph.value(product, self.ECOM_NS.stockLevel))
        if stock < quantity:
            return render(request, 'store/error.html', 
                        {'message': f'Insufficient stock. Only {stock} available'})
        
        # Create order
        order_id = str(uuid.uuid4())
        order = URIRef(self.ECOM_NS + order_id)
        
        self.graph.add((order, RDF.type, self.ECOM_NS.Order))
        self.graph.add((order, self.ECOM_NS.customer, Literal("John Doe", datatype=XSD.string)))
        self.graph.add((order, self.ECOM_NS.product, product))
        self.graph.add((order, self.ECOM_NS.quantity, Literal(quantity, datatype=XSD.integer)))
        self.graph.add((order, self.ECOM_NS.status, Literal("pending", datatype=XSD.string)))
        
        # Update stock
        self.graph.set((product, self.ECOM_NS.stockLevel, Literal(stock - quantity)))
        
        self.save_graph()
        return redirect('order_success')
    
# views.py
class ViewOrdersView(BaseOntologyView):
    def get(self, request):
        """Display all orders"""
        orders = []
        for order in self.graph.subjects(RDF.type, self.ECOM_NS.Order):
            try:
                # Get all values with safe fallbacks
                customer = str(self.graph.value(order, self.ECOM_NS.customer) or "Unknown")
                product = self.graph.value(order, self.ECOM_NS.product)
                
                # Handle case where product might not exist
                if product:
                    product_name = str(self.graph.value(product, self.ECOM_NS.name) or "Unknown Product")
                else:
                    product_name = "Unknown Product"
                
                # Handle missing quantity with safe conversion
                quantity_value = self.graph.value(order, self.ECOM_NS.quantity)
                quantity = int(quantity_value) if quantity_value is not None else 0
                
                # Handle missing status
                status = str(self.graph.value(order, self.ECOM_NS.status) or "unknown")
                
                # Extract order ID from URI, with fallback
                try:
                    order_id = str(order).split('#')[-1]
                except:
                    order_id = "unknown"
                
                orders.append({
                    'id': order_id,
                    'customer': customer,
                    'product': product_name,
                    'quantity': quantity,
                    'status': status
                })
            except Exception as e:
                # Log the error but continue processing other orders
                print(f"Error processing order {order}: {str(e)}")
                continue
            
        return render(request, 'store/admin/orders.html', {'orders': orders})

class AdminView(BaseOntologyView):
    def get(self, request):
        """Display admin dashboard"""
        # Create a new instance of ProductView to use its methods
        product_view = AdminProductView()
        products = product_view.get_all_products()
        return render(request, 'store/admin/dashboard.html', {'products': products})

    def post(self, request):
        """Handle adding new product"""
        product_name = request.POST.get('name')
        price = float(request.POST.get('price', 0))
        stock_level = int(request.POST.get('stock_level', 0))
        discount = float(request.POST.get('discount', 0))
        image = request.FILES.get('image')

        # Save the uploaded image to the media directory
        if image:
            image_path = os.path.join('product_images', image.name)
            with open(os.path.join(settings.MEDIA_ROOT, image_path), 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)

        product_id = product_name.lower().replace(" ", "_")
        product = URIRef(self.ECOM_NS + product_id)

        # Add product to graph
        self.graph.add((product, RDF.type, self.ECOM_NS.Product))
        self.graph.add((product, self.ECOM_NS.name, Literal(product_name, datatype=XSD.string)))
        self.graph.add((product, self.ECOM_NS.price, Literal(price, datatype=XSD.float)))
        self.graph.add((product, self.ECOM_NS.stockLevel, Literal(stock_level, datatype=XSD.integer)))
        self.graph.add((product, self.ECOM_NS.discount, Literal(discount, datatype=XSD.float)))
        self.graph.add((product, self.ECOM_NS.hasImage, Literal(image_path, datatype=XSD.string)))

        self.save_graph()
        return redirect('baseAdmin')
