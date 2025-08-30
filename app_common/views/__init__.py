from .member_views import (
    MemberRegistrationView,
    MemberLoginView,
    MemberProfileView,
    MemberListView,
    MemberDetailView
)
from .business_views import (
    BusinessRegistrationView,
    BusinessLoginView,
    BusinessProfileView,
    BusinessListView,
    BusinessDetailView,
    BusinessKycView
)
from .government_views import (
    GovernmentUserRegistrationView,
    GovernmentUserLoginView,
    GovernmentUserProfileView,
    GovernmentUserListView,
    GovernmentUserDetailView
)
from .staff_views import (
    StaffRegistrationView,
    StaffLoginView,
    StaffProfileView,
    StaffListView,
    StaffDetailView,
    StaffDashboardView
)

__all__ = [
    # Member views
    'MemberRegistrationView',
    'MemberLoginView', 
    'MemberProfileView',
    'MemberListView',
    'MemberDetailView',
    
    # Business views
    'BusinessRegistrationView',
    'BusinessLoginView',
    'BusinessProfileView', 
    'BusinessListView',
    'BusinessDetailView',
    'BusinessKycView',
    
    # Government views
    'GovernmentUserRegistrationView',
    'GovernmentUserLoginView',
    'GovernmentUserProfileView',
    'GovernmentUserListView', 
    'GovernmentUserDetailView',
    
    # Staff views
    'StaffRegistrationView',
    'StaffLoginView',
    'StaffProfileView',
    'StaffListView',
    'StaffDetailView',
    'StaffDashboardView',
]
