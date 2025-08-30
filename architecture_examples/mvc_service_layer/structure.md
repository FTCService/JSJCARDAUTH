# MVC with Service Layer Architecture

## Structure

```
app_name/
├── models/
│   ├── __init__.py
│   ├── member.py          # Member model
│   └── business.py        # Business model
├── controllers/
│   ├── __init__.py
│   ├── member_controller.py
│   └── business_controller.py
├── services/
│   ├── __init__.py
│   ├── member_service.py
│   └── business_service.py
├── serializers/
│   ├── __init__.py
│   ├── member_serializer.py
│   └── business_serializer.py
├── urls.py
└── admin.py
```

## Responsibilities

### Models (M)

- Data structure and validation
- Database relationships
- Simple business rules

### Controllers (C)

- HTTP request/response handling
- Input validation using serializers
- Calling appropriate services
- Response formatting

### Services (Business Logic)

- Complex business operations
- Data transformation
- External API calls
- Transaction management

### Serializers (View helpers)

- Input/output data transformation
- Request/response formatting

```

```
