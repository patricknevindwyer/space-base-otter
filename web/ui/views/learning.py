from django.shortcuts import render

def first(request):

    number = sean_add (3.141592653, 9.5)

    return render(request, "learning/first.html", context={"number": number})

def sean_add(a, b):
    c = a + b
    return c