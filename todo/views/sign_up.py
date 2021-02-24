from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages


from todo.forms import UserCreationForm

def sign_up(request):
    print(request.POST)
    #messages.warning(request, "test")
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        print(form)
        if form.is_valid():
            print("clean data")
            item = form.save(commit=False)
            print(form.cleaned_data)
            item.first_name = form.cleaned_data.get('first_name')
            item.last_name = form.cleaned_data.get('last_name')
            item.username = form.validate_username()
            if item.username == None:
                messages.warning(request, "Username/email not valid")
                return redirect('signup')

            print(item.last_name)
            item.email = form.cleaned_data.get('email')
            item.raw_password = form.clean_password2()
            if item.raw_password == None:
                messages.warning(request, "Passwords don't match")
                return redirect('signup')

            item.user = authenticate(username=item.email, password=item.raw_password)
            item.save()
            print(item)
            messages.success(request, "Account registerred! Please login with your account")
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'registration/sign_up.html', {'form': form})
