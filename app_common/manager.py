from django.contrib.auth.models import BaseUserManager

class MyAccountManager(BaseUserManager):
    """
    Custom user manager for handling staff and superuser creation.
    """
    
    def create_user(self, email, password=None, full_name=None, employee_id=None, is_staff=False,mobile_number=None, is_superuser=False, is_jobmitra=False, address=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            employee_id=employee_id,
            is_staff=is_staff,
            mobile_number=mobile_number,
            is_superuser=is_superuser,
            is_jobmitra=is_jobmitra,
            address=address
        )

        user.set_password(password)  # ✅ Hash Password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, full_name=None, employee_id=None):
        return self.create_user(
            email=email, 
            password=password, 
            full_name=full_name, 
            employee_id=employee_id,
            is_staff=True, 
            is_superuser=True
        )


class MemberManager(BaseUserManager):
    def create_user(self, mobile_number, pin, full_name, email=None):
        if not mobile_number:
            raise ValueError("mobile number is required")

        user = self.model(mobile_number=mobile_number, full_name=full_name, email=self.normalize_email(email))
        user.set_pin(pin)  # ✅ Hash PIN
        user.save(using=self._db)
        return user
    
    
class BusinessManager(BaseUserManager):
    def create_user(self, mobile_number, pin, business_name, email, is_institute=False, business_profile_image=None):
        if not mobile_number:
            raise ValueError("mobile number is required")

        user = self.model(mobile_number=mobile_number, business_name=business_name, email=self.normalize_email(email),is_institute=is_institute, business_profile_image=business_profile_image)
        user.set_pin(pin)  # ✅ Hash PIN
        user.save(using=self._db)
        return user
    
    
class GovernmentUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # ✅ Password hashing
        user.save(using=self._db)
        return user