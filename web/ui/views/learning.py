from django.shortcuts import render

def first(request):

    # Problem 00 - add two numbers
    number = sean_add (3.141592653, 9.5)

    # Problem 01 - Print string "Hi, I'm Sean."
    _01_string = "Hi, I'm Sean"

    # Problem 02 - Print string "Hi, I'm ...." with the name in a variable
    #name = "Sean"

    # Problem 03 - Print the list of numbers from 1 to 10

    # Problem 04 - Print the word "WORD" four times

    # Problem 05 - Build a LIST of 10 numbers to print out, doubling the number each time
    
    # Problem 06 - Use a list of numbers to print "# is less than five", "# is five", or "# is greater than 5"

    return render(request, "learning/first.html", context={
        "number": number,
        "_01": _01_string
    })


def sean_add(a, b):
    c = a + b
    return c