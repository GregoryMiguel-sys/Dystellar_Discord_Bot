def cont_primos(n) :
    es_primo = True
    cont_divs = 0

    for i in range(1, n + 1) :
        if n % i == 0 :
            cont_divs += 1
            if cont_divs == 2 :
                es_primo = True
            else :
                es_primo = False

    return es_primo

num = int(input())
es_primo = cont_primos(num)
if cont_primos(num) :
    print(f"El número {num} SI es PRIMO")
else :
    print(f"El número {num} NO es primo")