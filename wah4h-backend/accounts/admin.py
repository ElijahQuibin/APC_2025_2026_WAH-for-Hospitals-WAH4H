"""
accounts/admin.py
Django Admin Configuration for Identity & Structure Management

Special Considerations:
- User model has practitioner as OneToOneField (PK), requiring special handling
- Enhanced search capabilities for LGU hospital staff
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import (
    Organization,
    Location,
    Practitioner,
    PractitionerRole,
    User,
    Endpoint,
    HealthcareService
)


ROLE_HELP = (
    'Frontend modules require one of: doctor, nurse, lab_technician, '
    'pharmacist, billing_clerk.'
)


class UserCreationForm(forms.ModelForm):
    """Admin form for creating users with hashed passwords."""

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'status',
            'is_staff',
            'is_active',
            'is_superuser',
            'practitioner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['practitioner'].required = False
        self.fields['practitioner'].help_text = (
            'Optional. Leave blank to auto-create a Practitioner for this user.'
        )
        self.fields['status'].initial = 'active'
        self.fields['role'].initial = 'doctor'
        self.fields['role'].help_text = ROLE_HELP

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        extras = {
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'role': self.cleaned_data.get('role') or 'doctor',
            'status': self.cleaned_data.get('status') or 'active',
            'is_staff': self.cleaned_data.get('is_staff', False),
            'is_active': self.cleaned_data.get('is_active', True),
            'is_superuser': self.cleaned_data.get('is_superuser', False),
        }
        practitioner = self.cleaned_data.get('practitioner')
        if practitioner is not None:
            extras['practitioner'] = practitioner

        # create_user hashes the password and creates a Practitioner when needed
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data['password1'],
            **extras,
        )
        # ModelForm normally sets this when save(commit=False) is used.
        # Admin always calls form.save_m2m() afterward.
        self.save_m2m = lambda: None
        return user


class UserChangeForm(forms.ModelForm):
    """Admin form for editing users; optional password reset."""

    password = ReadOnlyPasswordHashField(
        label='Password',
        help_text=(
            'Raw passwords are not stored, so there is no way to see this '
            "user's password. Set a new password below to change it."
        ),
    )
    password1 = forms.CharField(
        label='New password',
        required=False,
        widget=forms.PasswordInput,
        help_text='Leave blank to keep the current password.',
    )
    password2 = forms.CharField(
        label='Confirm new password',
        required=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role',
            'status',
            'is_staff',
            'is_active',
            'is_superuser',
            'practitioner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].help_text = ROLE_HELP

    def clean_password(self):
        # Return the initial value regardless of what the user provides
        return self.initial.get('password')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError(
                    "The two password fields didn't match."
                )
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        if password1:
            user.set_password(password1)
        if commit:
            user.save()
        return user


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization management."""
    
    list_display = (
        'organization_id',
        'name',
        'nhfr_code',
        'type_code',
        'active',
        'status'
    )
    search_fields = ('name', 'nhfr_code', 'type_code', 'address_city')
    list_filter = ('active', 'status', 'type_code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'active',
                'nhfr_code',
                'type_code',
                'name',
                'alias',
                'status'
            )
        }),
        ('Contact Information', {
            'fields': (
                'telecom',
                'endpoint',
            )
        }),
        ('Address', {
            'fields': (
                'address_line',
                'address_city',
                'address_district',
                'address_state',
                'address_country',
                'address_postal_code',
            )
        }),
        ('Contact Person', {
            'fields': (
                'contact_purpose',
                'contact_first_name',
                'contact_last_name',
                'contact_telecom',
                'contact_address_line',
                'contact_address_city',
                'contact_address_state',
                'contact_address_country',
                'contact_postal_code',
            ),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('part_of_organization',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin interface for Location management."""
    
    list_display = (
        'location_id',
        'name',
        'identifier',
        'physical_type_code',
        'type_code',
        'operational_status',
        'status'
    )
    search_fields = (
        'name',
        'identifier',
        'physical_type_code',
        'type_code',
        'address_city'
    )
    list_filter = ('operational_status', 'status', 'mode', 'physical_type_code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'identifier',
                'status',
                'name',
                'alias',
                'description',
                'physical_type_code',
                'type_code',
                'operational_status',
                'mode',
            )
        }),
        ('Contact & Location', {
            'fields': (
                'telecom',
                'longitude',
                'latitude',
                'altitude',
            )
        }),
        ('Address', {
            'fields': (
                'address_line',
                'address_city',
                'address_district',
                'address_state',
                'address_country',
                'address_postal_code',
            )
        }),
        ('Hours of Operation', {
            'fields': (
                'hours_of_operation_days',
                'hours_of_operation_all_day',
                'opening_time',
                'closing_time',
                'availability_exceptions',
            ),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': (
                'managing_organization',
                'part_of_location',
                'endpoint',
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    """
    Admin interface for Practitioner management.
    
    Enhanced search for LGU hospital staff to quickly find practitioners by:
    - Name (first_name, last_name)
    - Identifier (hospital/system ID)
    - PRC License (qualification_identifier)
    """
    
    list_display = (
        'practitioner_id',
        'identifier',
        'first_name',
        'last_name',
        'qualification_identifier',
        'active',
        'gender',
        'status'
    )
    search_fields = (
        'first_name',
        'last_name',
        'identifier',
        'qualification_identifier',  # PRC License search
        'telecom',
        'address_city'
    )
    list_filter = ('active', 'gender', 'status', 'qualification_code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Identification', {
            'fields': (
                'identifier',
                'active',
                'status',
            )
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'middle_name',
                'last_name',
                'suffix_name',
                'gender',
                'birth_date',
                'photo_url',
            )
        }),
        ('Contact Information', {
            'fields': (
                'telecom',
                'communication_language',
            )
        }),
        ('Address', {
            'fields': (
                'address_line',
                'address_city',
                'address_district',
                'address_state',
                'address_country',
                'address_postal_code',
            ),
            'classes': ('collapse',)
        }),
        ('Professional Qualifications (PRC)', {
            'fields': (
                'qualification_code',
                'qualification_identifier',
                'qualification_issuer',
                'qualification_period_start',
                'qualification_period_end',
            ),
            'description': 'Professional Regulation Commission (PRC) license information'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PractitionerRole)
class PractitionerRoleAdmin(admin.ModelAdmin):
    """Admin interface for PractitionerRole management."""
    
    list_display = (
        'practitioner_role_id',
        'practitioner',
        'organization',
        'location',
        'role_code',
        'specialty_code',
        'active',
        'status'
    )
    search_fields = (
        'practitioner__last_name',
        'practitioner__first_name',
        'organization__name',
        'role_code',
        'specialty_code',
        'identifier'
    )
    list_filter = ('active', 'status', 'role_code', 'specialty_code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'identifier',
                'active',
                'status',
            )
        }),
        ('Assignment', {
            'fields': (
                'practitioner',
                'organization',
                'location',
                'healthcare_service',
            )
        }),
        ('Role Details', {
            'fields': (
                'role_code',
                'specialty_code',
                'telecom',
                'period_start',
                'period_end',
            )
        }),
        ('Availability', {
            'fields': (
                'available_days_of_week',
                'available_all_day_flag',
                'available_start_time',
                'available_end_time',
                'availability_exceptions',
            ),
            'classes': ('collapse',)
        }),
        ('Not Available Periods', {
            'fields': (
                'not_available_description',
                'not_available_period_start',
                'not_available_period_end',
            ),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('endpoint',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Admin interface for User management.

    Special Handling:
    - User.practitioner is a OneToOneField used as Primary Key
    - Practitioner is optional on create (auto-created when blank)
    - Passwords are hashed via set_password / create_user
    """

    add_form = UserCreationForm
    form = UserChangeForm

    list_display = (
        'practitioner',
        'username',
        'email',
        'role',
        'status',
        'is_staff',
        'last_login',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'practitioner__first_name',
        'practitioner__last_name',
    )
    list_filter = ('role', 'status', 'is_staff', 'is_active')
    readonly_fields = ('last_login', 'created_at', 'updated_at')

    fieldsets = (
        ('Practitioner Link', {
            'fields': ('practitioner',),
        }),
        ('Account Information', {
            'fields': (
                'username',
                'email',
                'password',
                'password1',
                'password2',
            )
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
            )
        }),
        ('Permissions & Status', {
            'fields': (
                'role',
                'status',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
        ('Metadata', {
            'fields': (
                'last_login',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ('Practitioner Link', {
            'fields': ('practitioner',),
            'description': (
                'Optional. Leave blank to auto-create a Practitioner. '
                'Each Practitioner can only have one User account.'
            ),
        }),
        ('Account Information', {
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
            )
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
            )
        }),
        ('Permissions & Status', {
            'fields': (
                'role',
                'status',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
            'description': ROLE_HELP,
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        defaults = {'form': self.add_form if obj is None else self.form}
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing User — lock practitioner link
            return self.readonly_fields + ('practitioner',)
        return self.readonly_fields

    def save_form(self, request, form, change):
        # create_user already persists the row on add
        if not change:
            return form.save(commit=True)
        return super().save_form(request, form, change)

    def save_model(self, request, obj, form, change):
        if change:
            form.save(commit=True)
        # On add, object was already saved in save_form via create_user

    def save_related(self, request, form, formsets, change):
        # Creation form bypasses ModelForm.save(commit=False), so ensure
        # save_m2m exists before the default admin related-save path runs.
        if not hasattr(form, 'save_m2m'):
            form.save_m2m = lambda: None
        super().save_related(request, form, formsets, change)


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    """Admin interface for Endpoint management."""
    
    list_display = (
        'endpoint_id',
        'name',
        'connection_type',
        'managing_organization',
        'status'
    )
    search_fields = ('name', 'connection_type', 'address')
    list_filter = ('status', 'connection_type')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(HealthcareService)
class HealthcareServiceAdmin(admin.ModelAdmin):
    """Admin interface for HealthcareService management."""
    
    list_display = (
        'healthcare_service_id',
        'name',
        'active',
        'status'
    )
    search_fields = ('name',)
    list_filter = ('active', 'status')
    readonly_fields = ('created_at', 'updated_at')
