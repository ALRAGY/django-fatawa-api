# Django Fatawa API

A robust Django REST API with advanced permission synchronization system for Fatawa management.

## 🚀 Features

- **Advanced Permission System**: Role-based and custom user permissions with real-time synchronization
- **High Performance**: Intelligent caching and bulk operations for scalability
- **Data Integrity**: Atomic transactions and conflict detection
- **RESTful API**: Complete CRUD operations with JWT authentication
- **Docker Support**: Containerized deployment with PostgreSQL
- **Comprehensive Testing**: Full test suite for all components

## 📁 Project Structure

```
fatawa/
├── accounts/                    # Main app with user management
│   ├── models.py              # User, Role, Permission models
│   ├── serializers.py         # API serializers
│   ├── enhanced_views.py      # Enhanced API views
│   ├── permission_sync.py     # Permission synchronization system
│   ├── permission_bulk.py    # Bulk operations and analytics
│   ├── permissions.py        # Custom permission classes
│   ├── tests.py             # Comprehensive test suite
│   └── management/          # Django management commands
├── fatawa_api/               # Django project settings
│   ├── settings.py           # Configuration with environment support
│   ├── urls.py              # Main URL routing
│   └── wsgi.py              # WSGI deployment
├── docker-compose.yml          # Docker orchestration
├── Dockerfile               # Container configuration
├── requirements.txt          # Python dependencies
└── .env.example            # Environment variables template
```

## 🔧 Installation & Setup

### Local Development
```bash
# Clone the repository
git clone <repository-url>
cd fatawa

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up --build

# Or in detached mode
docker-compose up -d --build
```

## 📚 API Documentation

### Base URL
- Local: `http://localhost:8000/api/auth/`
- Production: `https://your-domain.com/api/auth/`

### Documentation
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **Admin Panel**: `http://localhost:8000/admin/`

## 🔐 Authentication

### JWT Login
```bash
curl -X POST http://localhost:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

### Use Token
```bash
curl -X GET http://localhost:8000/api/auth/users/profile/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🛠️ Permission System

### Role-Based Permissions
```bash
# Create role
curl -X POST http://localhost:8000/api/auth/roles/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "role_name": "Editor",
    "description": "Can edit content"
  }'

# Assign permissions to role
curl -X POST http://localhost:8000/api/auth/role-permissions/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "role_id": 1,
    "permission_id": 1
  }'
```

### Custom User Permissions
```bash
# Grant custom permission
curl -X POST http://localhost:8000/api/auth/users/1/grant_permission/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "permission_id": 1
  }'

# Bulk assign permissions
curl -X POST http://localhost:8000/api/auth/user-permissions/bulk_assign/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "permission_ids": [1, 2, 3]
  }'
```

## 📊 System Management

### Permission Analytics
```bash
# View analytics
curl -X GET http://localhost:8000/api/auth/system/permission_analytics/ \
  -H "Authorization: Bearer TOKEN"
```

### Sync Commands
```bash
# Force sync all permissions
python manage.py sync_permissions --force

# View analytics
python manage.py sync_permissions --analytics

# Check conflicts
python manage.py sync_permissions --check-conflicts
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific test
python manage.py test accounts.tests.PermissionSyncTestCase

# Test with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🔧 Environment Variables

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=sqlite:///db.sqlite3  # For local development
# DB_NAME=fatawa_db         # For PostgreSQL
# DB_USER=postgres
# DB_PASSWORD=postgres
# DB_HOST=localhost
# DB_PORT=5432

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 🚀 Deployment

### Production Setup
1. **Environment**: Set `DEBUG=False` and configure production database
2. **Security**: Generate new `SECRET_KEY` and `JWT_SECRET_KEY`
3. **Database**: Configure PostgreSQL with proper credentials
4. **Static Files**: Collect static files with `python manage.py collectstatic`
5. **Web Server**: Configure Nginx/Apache with Gunicorn/uWSGI

### Docker Production
```bash
# Build production image
docker build -t fatawa-api .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e DEBUG=False \
  -e SECRET_KEY=your-production-secret \
  -e DB_NAME=fatawa_db \
  -e DB_USER=postgres \
  -e DB_PASSWORD=your-password \
  fatawa-api
```

## 📈 Performance Features

- **Intelligent Caching**: 5-minute cache with smart invalidation
- **Bulk Operations**: Optimized for large-scale permission management
- **Database Optimization**: Efficient queries with `select_related`
- **Signal-Based Sync**: Real-time permission updates
- **Conflict Detection**: Automatic identification of permission inconsistencies

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based authentication
- **Permission-Based Access**: Granular control over API endpoints
- **CORS Configuration**: Proper cross-origin resource sharing
- **CSRF Protection**: Built-in Django CSRF middleware
- **Input Validation**: Comprehensive serializer validation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test
4. Commit changes: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs/`
- Review the test cases for usage examples

---

**Built with ❤️ using Django, Django REST Framework, and PostgreSQL**
