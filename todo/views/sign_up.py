from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages


from todo.forms import UserCreationForm
from todo.models import Group

def sign_up(request):
    #print(request.POST)
    group = Group.objects.get(name="Engineer")
    #messages.warning(request, "test")
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        #print(form)
        if form.is_valid():
            #print("clean data")
            item = form.save(commit=False)
            #print(form.cleaned_data)
            item.first_name = form.cleaned_data.get('first_name')
            item.last_name = form.cleaned_data.get('last_name')
            if form.validate_username() != None:
                item.username = form.validate_username().lower()
            else:
                messages.warning(request, "Username/email not valid")
                return redirect('signup')

            ##print(item.last_name)
            item.email = form.cleaned_data.get('email')
            item.raw_password = form.clean_password2()
            if item.raw_password == None:
                messages.warning(request, "Passwords don't match")
                return redirect('signup')

            item.user = authenticate(username=item.email, password=item.raw_password)
            item.save()
            #print(item)
            group.user_set.add(item)

            messages.success(request, "Account registerred! Please login with your account")
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'registration/sign_up.html', {'form': form})
