
# AETHER STORE (Multi-Agent E-Commerce Platform)

---

AETHER STORE is an innovative e-commerce platform that goes beyond traditional concepts by implementing a multi-agent system. It uses specialized autonomous agents to manage various aspects of the platform, such as customer interactions, product recommendations, inventory, and feedback analysis. This decentralized approach optimizes operations, enhances user experiences, and ensures scalability.


## Ontology in the AETHER STORE MAS

The AETHER STORE Multi-Agent E-Commerce Platform aims to simulate the functioning of an advanced e-commerce system using an ontology-based approach. The ontology captures the core entities, their relationships, and behaviors within the system, such as customers, products, orders, agents, and tasks. By using an ontology, the platform allows for efficient reasoning, data sharing, and task management across different agents, ensuring that they can work collaboratively to optimize the e-commerce processes. 

![Screenshot1](https://github.com/user-attachments/assets/7b5a0f2a-9afc-4272-b100-d5127169cd8f)



## Technologies Used
- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (default Django database)
- **Version Control**: Git


## Setup Instructions

### Prerequisites
- Python 3.x
- Django (version compatible with the project)
- Git

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Kesara-Hansajith/AETHER-STORE--multiagent_ecommerce_platform.git
   ```
2. Navigate to the project directory:
   ```bash
   cd ecommerce_project
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```
6. Access the platform via:
   - **Admin Dashboard**: `http://127.0.0.1:8000/admin`
   - **Main Application**: `http://127.0.0.1:8000`

---

## Project Structure

```plaintext
|-- ecommerce_project/
    |-- db.sqlite3          # Database file
    |-- manage.py           # Django management script
    |-- requirements.txt    # Python dependencies
    |-- ecommerce_platform/ # Core Django application files
        |-- settings.py     # Django settings
        |-- urls.py         # Project URL configurations
    |-- store/              # Main application
        |-- models.py       # Database models
        |-- views.py        # Application logic
        |-- templates/      # HTML templates
        |-- static/         # Static files (CSS, JS, images)
```

---

## Contribution

If you wish to contribute to this project:
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Description of changes"
   ```
4. Push to your forked repository and create a pull request.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---


