from django.contrib import admin
from django.urls import path, include
from helpers import swagger_documentation

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('api/', include('app_common.urls')),
    path('admin/', include('admin_dashboard.urls')),
    path('member/', include('member.urls')),
    path('campaign_management/', include('campaign_management.urls')),
    path('swagger/', swagger_documentation.schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', swagger_documentation.schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
