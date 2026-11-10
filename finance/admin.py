from django.contrib import admin
from django.utils.html import format_html

from finance.models import Bank, InvitationCode


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo_preview', 'cashback_categories_limit']
    search_fields = ['name']
    fields = ['name', 'image', 'cashback_categories_limit']

    @admin.display(description='Logo')
    def logo_preview(self, obj):
        if not obj.image:
            return '-'
        return format_html(
            '<img src="{}" style="width: 32px; height: 32px; object-fit: contain;" />',
            obj.image.url,
        )


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'created_by', 'created_at', 'used_by', 'used_at']
    list_filter = ['created_at', 'used_at']
    search_fields = ['code', 'created_by__username', 'used_by__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {'fields': ('code', 'created_by')}),
        ('Usage', {'fields': ('used_by', 'used_at')}),
    )
    
    actions = ['generate_invitation_codes']
    
    def generate_invitation_codes(self, request, queryset):
        for _ in queryset:
            InvitationCode.generate_code(request.user)
        self.message_user(request, f'{len(queryset)} new invitation code(s) generated.')
    generate_invitation_codes.short_description = 'Generate new invitation codes'
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.code:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
