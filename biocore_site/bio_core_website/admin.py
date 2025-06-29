from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Category, Element, Manufacturer, Vitamin, Consultation, VitaminLevel, UserBMI, PromoVideo

admin.site.register(Category)
admin.site.register(Manufacturer)
admin.site.register(Vitamin)
admin.site.register(Consultation)
admin.site.register(VitaminLevel)
admin.site.register(UserBMI)
admin.site.register(PromoVideo)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительная информация", {
            "fields": ("gender", "weight", "height", "age")
        }),
    )
class ElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'display_manufacturers')
    list_filter = ('category', 'manufacturers')
    filter_horizontal = ('manufacturers',)  # Для удобного выбора производителей
    
    def display_manufacturers(self, obj):
        return ", ".join([m.name for m in obj.manufacturers.all()])
    display_manufacturers.short_description = 'Производители'

admin.site.register(Element, ElementAdmin)