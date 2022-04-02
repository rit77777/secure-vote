from django.contrib import admin

# Register your models here.

from .models import  Party, RegisteredVoters, UniqueID, Constituency


admin.site.site_header = "Secure Voting Admin"
admin.site.site_title = "Secure Voting Admin Area"
admin.site.index_title = "Welcome to the Secure Voting admin area"

class PartyInline(admin.TabularInline):
    model = Party


class ConstituencyAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['c_id', 'c_name', 'is_active', 'node_address']}),
                 ('Date Information', {'fields': ['pub_date'], 'classes': ['collapse']}), ]
    inlines = [PartyInline]


admin.site.register(RegisteredVoters)
admin.site.register(UniqueID)
admin.site.register(Constituency, ConstituencyAdmin)
# admin.site.register(Party)
# admin.site.register(Constituency)