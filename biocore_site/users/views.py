from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm  # импорт своей формы

def register(request):
    if request.method != 'POST':
        form = CustomUserCreationForm()
    else:
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user)
            return redirect('bio_core_website:home')  # поменяй на нужный URL
    context = {'form': form}
    return render(request, 'registration/register.html', context)
