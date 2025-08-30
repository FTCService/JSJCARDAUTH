# JSJ Card Authentication System

A Django-based authentication and card management system with REST API capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd JSJCARDAUTH
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv

   # On macOS/Linux
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**

   Create a `.env` file in the root directory with the following variables:

   ```env
   # Django Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True

   # Database Configuration
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=localhost

   # External Services
   EVENT_SERVER_URL=http://your-event-server-url
   REWARD_SERVER_URL=http://your-reward-server-url
   JOB_SERVER_URL=http://your-job-server-url
   ```

5. **Database Setup**

   Make sure PostgreSQL is running and create a database:

   ```sql
   CREATE DATABASE your_database_name;
   CREATE USER your_database_user WITH PASSWORD 'your_database_password';
   GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_database_user;
   ```

6. **Run Database Migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create Superuser (Optional)**

   ```bash
   python manage.py createsuperuser
   ```

8. **Collect Static Files**

   ```bash
   python manage.py collectstatic --noinput
   ```

9. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`

## 📚 API Documentation

- **Swagger UI**: `http://127.0.0.1:8000/swagger/`
- **ReDoc**: `http://127.0.0.1:8000/redoc/`

## 🏗️ Project Structure

```
JSJCARDAUTH/
├── admin_dashboard/     # Admin dashboard functionality
├── app_common/          # Common app with user models and authentication
├── campaign_management/ # Campaign management features
├── crm/                # Customer relationship management
├── member/             # Member management
├── helpers/            # Utility functions and documentation
├── templates/          # Email templates
├── staticfiles/        # Static files
├── jsjcardauth/        # Main Django project settings
└── manage.py           # Django management script
```

## 🔧 Key Features

- **Multi-tenant Authentication**: Support for Members, Admins, and Government users
- **REST API**: Full REST API with Django REST Framework
- **JWT Authentication**: Token-based authentication using SimpleJWT
- **PostgreSQL Database**: Production-ready database setup
- **CORS Support**: Cross-origin resource sharing enabled
- **Email Integration**: SMTP email configuration
- **API Documentation**: Automated API docs with Swagger/ReDoc

## 🔐 Authentication Backends

The system includes custom authentication backends:

- `MemberAuthBackend`: For member users
- `AdminAuthBackend`: For admin users
- `GovernmentAuthBackend`: For government users

## 📊 Available Apps

1. **app_common**: Core functionality, user models, and authentication
2. **admin_dashboard**: Administrative interface and controls
3. **member**: Member management and operations
4. **campaign_management**: Marketing campaign features
5. **crm**: Customer relationship management tools

## 🌐 API Endpoints

Main API routes are available under:

- `/api/` - Common API endpoints
- `/admin/` - Admin dashboard endpoints
- `/member/` - Member-specific endpoints
- `/crm/` - CRM endpoints
- `/campaign_management/` - Campaign management endpoints

## ⚙️ Configuration

### Database Options

The project is configured for PostgreSQL by default. For development, you can also use SQLite by modifying `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Email Configuration

Email is configured to use Gmail SMTP. Update the email settings in `settings.py` as needed:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## 🚀 Deployment

For production deployment:

1. Set `DEBUG=False` in your `.env` file
2. Configure proper `ALLOWED_HOSTS` in settings
3. Use a production-grade database
4. Set up proper static file serving
5. Configure environment variables securely

## 🛠️ Development

### Running Tests

```bash
python manage.py test
```

### Creating New Apps

```bash
python manage.py startapp app_name
```

### Database Operations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

## 📝 Dependencies

Key packages used in this project:

- **Django 5.2**: Web framework
- **Django REST Framework**: API development
- **SimpleJWT**: JWT authentication
- **psycopg2**: PostgreSQL adapter
- **django-cors-headers**: CORS handling
- **drf-yasg**: API documentation
- **python-dotenv**: Environment variable management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests for new functionality
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error**

   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify database exists

2. **Migration Issues**

   ```bash
   python manage.py migrate --fake-initial
   ```

3. **Static Files Not Loading**

   ```bash
   python manage.py collectstatic --clear
   ```

4. **Import Errors**
   - Ensure virtual environment is activated
   - Check if all dependencies are installed

For more help, check the Django documentation or create an issue in the repository.
