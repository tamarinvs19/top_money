from django.contrib import admin
from finance.models import InvitationCode


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
