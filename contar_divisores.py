def contar_divs(n) :
    cont_divs = 0
    aux_n = n

    if n < 0 :
        n *= -1

    for i in range(1, n + 1) :
        if aux_n % i == 0 :
            cont_divs += 1

    return cont_divs

n = int(input())
contador_divisores = contar_divs(n)
if n != 0 :
    print(f"El número {n} tiene {contador_divisores} divisores")