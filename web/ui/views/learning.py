from django.shortcuts import render

def first(request):

    # Problem 00 - add two numbers
    number = sean_add (3.141592653, 9.5)

    # Problem 01 - Print string "Hi, I'm Sean."
    string_1 = "Hi, I'm Sean"

    # Problem 02 - Print string "Hi, I'm ...." with the name in a variable
    name = "dad"
    string_2 = "Hi, I`m " + name
    string_2_a = "Hi, I'm %s, and %s. We like the number %f." % (name, string_1, number)

    # Problem 03 - Print the list of numbers from 1 to 10
    list_3 = 1,2,3,4,5,6,7,8,9,10
    #list_3_a =
    #var_3 = 1
    # Problem 04 - Print the word "WORD" four times

    # Problem 05 - Build a LIST of 10 numbers to print out, doubling the number each time
    
    # Problem 06 - Use a list of numbers to print "# is less than five", "# is five", or "# is greater than 5"









    return render(request, "learning/first.html", context={
        "number": number,
        "string_1": string_1,
        "string_2": string_2,
        "string_2_a": string_2_a
    })


def sean_add(a, b):
    c = a + b
    return c

















#def crash_escape = 1