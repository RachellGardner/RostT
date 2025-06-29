from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Element, Vitamin, Consultation, VitaminLevel, UserBMI
from django.contrib.auth.decorators import login_required
from .forms import ProfileEditForm, ConsultationForm, SearchForm
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from .models import PromoVideo, Manufacturer
from django.core.cache import cache 
from django.views.decorators.cache import cache_page
from .models import Category
from django.db import transaction, models  # Добавлен импорт models
from django.db.models import Prefetch, Count

@login_required
def consultation_view(request):
    cache_key = f'user_{request.user.id}_consultation_vitamins'
    vitamins = cache.get(cache_key)
    
    if not vitamins:
        vitamins = Vitamin.objects.select_related('element').only(
            'id', 'name', 'min_normal', 'max_normal', 'unit', 
            'danger_high_level', 'high_level_message', 'element__id'
        )
        cache.set(cache_key, vitamins, 60*60*12)  # 12 часов кэша
    
    form_cache_key = f'user_{request.user.id}_consultation_form_data'
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST, vitamins=vitamins)
        if form.is_valid():
            try:
                with transaction.atomic():
                    consultation = Consultation.objects.create(
                        user=request.user,
                        notes=form.cleaned_data['notes']
                    )
                    
                    vitamin_levels = [
                        VitaminLevel(
                            consultation=consultation,
                            vitamin_id=vitamin.id,
                            value=form.cleaned_data[f'vitamin_{vitamin.id}']
                        ) for vitamin in vitamins
                    ]
                    VitaminLevel.objects.bulk_create(vitamin_levels)
                    
                    # Очищаем кэш результатов предыдущих консультаций
                    cache.delete_many([
                        f'user_{request.user.id}_consultation_results',
                        f'user_{request.user.id}_consultation_history'
                    ])
                    
                    request.session['consultation_id'] = consultation.id
                    messages.success(request, 'Данные сохранены!')
                    return redirect('bio_core_website:consultation_results')
            except Exception as e:
                messages.error(request, f'Ошибка: {e}')
                # Сохраняем данные формы в кэш при ошибке
                cache.set(form_cache_key, request.POST, 60*30)
    else:
        form_data = cache.get(form_cache_key)
        form = ConsultationForm(vitamins=vitamins, data=form_data)
        if form_data:
            cache.delete(form_cache_key)
    
    return render(request, 'bio_core_website/consultation.html', {
        'form': form,
        'vitamins': vitamins
    })

@login_required
def consultation_results(request):
    consultation_id = request.session.get('consultation_id')
    if not consultation_id:
        return redirect('bio_core_website:consultation')
    
    cache_key = f'user_{request.user.id}_consultation_results_{consultation_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'bio_core_website/consultation_results.html', cached_data)
    
    consultation = get_object_or_404(Consultation, id=consultation_id)
    levels = consultation.vitamin_levels.select_related('vitamin')
    
    deficient_elements = []
    excess_vitamins = []
    
    for level in levels:
        if level.value < level.vitamin.min_normal and level.vitamin.element:
            deficient_elements.append(level.vitamin.element)
        elif level.vitamin.danger_high_level and level.value > level.vitamin.max_normal:
            excess_vitamins.append({
                'vitamin': level.vitamin,
                'value': level.value,
                'message': level.vitamin.high_level_message
            })
    
    context = {
        'elements': deficient_elements,
        'excess_vitamins': excess_vitamins,
        'consultation_date': consultation.date
    }
    
    cache.set(cache_key, context, 60*60*24)  # Кэш на 24 часа
    
    return render(request, 'bio_core_website/consultation_results.html', context)

@login_required
def consultation_history(request):
    cache_key = f'user_{request.user.id}_consultation_history'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        consultations = cached_data['consultations']
        chart_data = cached_data['chart_data']
    else:
        consultations = request.user.consultations.select_related('user').prefetch_related(
            Prefetch('vitamin_levels', queryset=VitaminLevel.objects.select_related('vitamin'))
        )[:10]
        
        vitamins = Vitamin.objects.only('id', 'name', 'unit', 'min_normal', 'max_normal')
        chart_data = {}
        
        for vitamin in vitamins:
            levels = VitaminLevel.objects.filter(
                vitamin=vitamin,
                consultation__user=request.user
            ).only('value', 'consultation__date').order_by('consultation__date')
            
            chart_data[vitamin.name] = {
                'dates': [l.consultation.date.strftime('%Y-%m-%d') for l in levels],
                'values': [l.value for l in levels],
                'unit': vitamin.unit,
                'min_normal': vitamin.min_normal,
                'max_normal': vitamin.max_normal
            }
        
        cache.set(cache_key, {
            'consultations': consultations,
            'chart_data': chart_data
        }, 60*60*12)  # 12 часов кэша
    
    return render(request, 'bio_core_website/consultation_history.html', {
        'consultations': consultations,
        'chart_data': chart_data
    })

@login_required
def profile_view(request):
    user = request.user
    cache_key = f'user_{user.id}_bmi_data'
    bmi_data = cache.get(cache_key)
    
    if not bmi_data and user.weight and user.height:
        bmi = UserBMI.calculate_bmi(user.weight, user.height)
        category = UserBMI.get_bmi_category(bmi)
        bmi_data = {
            'value': round(bmi, 1),
            'category': category,
            'history': list(user.bmi_history.only('date', 'weight', 'height', 'bmi', 'category')[:10])
        }
        cache.set(cache_key, bmi_data, 60*60)  # 1 час кэша
    
    return render(request, 'bio_core_website/profile.html', {
        'user': user,
        'bmi_data': bmi_data
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            if form.cleaned_data.get('delete_avatar') and request.user.avatar:
                request.user.avatar.delete(save=False)
                request.user.avatar = None
            
            form.save()
            
            # Очищаем кэш профиля
            cache.delete(f'user_{request.user.id}_bmi_data')
            cache.delete(f'user_{request.user.id}_consultation_history')
            
            messages.success(request, 'Профиль обновлен!')
            return redirect('bio_core_website:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'bio_core_website/edit_profile.html', {'form': form})

def home(request):
    categories = Category.objects.all()[:2]
    return render(request, 'bio_core_website/home.html', {'categories': categories})

def category_elements(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    elements = category.elements.all()
    return render(request, 'bio_core_website/category_elements.html', {
        'category': category,
        'elements': elements
    })
def element_detail(request, pk):
    element = get_object_or_404(Element, id=pk)
    return render(request, 'bio_core_website/element_detail.html', {
        'element': element
    })

@cache_page(60 * 60)  # Кэширование на 1 час
def catalog_view(request):
    cache_key = 'full_catalog_data'
    data = cache.get(cache_key)
    
    if not data:
        categories = Category.objects.prefetch_related(
            Prefetch('elements',
                   queryset=Element.objects.select_related('category')
                                         .prefetch_related('manufacturers')
                                         .only('id', 'name', 'image', 'description', 'category__name')
            )
        ).annotate(element_count=Count('elements')).only('id', 'name', 'image')
        
        data = {
            'categories': categories,
            'title': 'Полный каталог продукции'
        }
        cache.set(cache_key, data, 60 * 60 * 12)  # Кэш на 12 часов
    
    return render(request, 'bio_core_website/catalog.html', data)

def element_detail(request, pk):
    element = get_object_or_404(
        Element.objects.select_related('category')
                      .prefetch_related('manufacturers', 'vitamin_data'),
        id=pk
    )
    return render(request, 'bio_core_website/element_detail.html', {
        'element': element,
        'title': element.name
    })

def about_view(request):
    cache_key = 'promo_video'
    promo_video = cache.get(cache_key)
    
    if not promo_video:
        promo_video = PromoVideo.objects.filter(is_active=True).only('title', 'video_file').first()
        cache.set(cache_key, promo_video, 60 * 60 * 24)  # Кэш на 24 часа
    
    return render(request, 'bio_core_website/about.html', {
        'title': 'О компании',
        'promo_video': promo_video
    })

def search_element(request):
    form = SearchForm()
    results = None
    query = None
    
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query'].strip().lower()
            cache_key = f'search_results_{query[:50]}'  # Ограничиваем длину ключа
            
            results = cache.get(cache_key)
            
            if not results:
                results = list(Element.objects.filter(name__icontains=query).only(
                    'id', 'name', 'category__name', 'image'
                )[:20])
                cache.set(cache_key, results, 60*60*6)  # 6 часов кэша
    
    # Кэшируем популярные запросы
    popular_searches = cache.get_or_set('popular_searches', [
        'Витамин C', 'Магний', 'Цинк', 'Омега-3'
    ], 60*60*24)
    
    return render(request, 'bio_core_website/search_results.html', {
        'form': form,
        'results': results,
        'query': query,
        'popular_searches': popular_searches
    })
