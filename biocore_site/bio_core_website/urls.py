from django.urls import path
from . import views
from .views import profile_view, edit_profile
from django.conf import settings
from django.conf.urls.static import static

app_name = 'bio_core_website'  # Пространство имен приложения

urlpatterns = [
    path('', views.home, name='home'),  # Главная страница
    path('category/<int:category_id>/', views.category_elements, name='category_elements'),
    path('element/<int:pk>/', views.element_detail, name='element_detail'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('consultation/', views.consultation_view, name='consultation'),
    path('consultation/results/', views.consultation_results, name='consultation_results'),
    path('consultation/history/', views.consultation_history, name='consultation_history'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('about/', views.about_view, name='about'),
    path('search/',  views.search_element, name='search'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)