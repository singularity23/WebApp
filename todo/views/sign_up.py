from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages


from todo.forms import UserCreationForm

def sign_up(request):
    print(request.POST)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        print(form)
        if form.is_valid():
            print("clean data")
            form.save()
            first_name = form.cleaned_data.get('first_nanme')
            last_name = form.cleaned_data.get('last_nanme')
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, "Account registerred! Please login with your account")
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'registration/sign_up.html', {'form': form})
