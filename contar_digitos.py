def cont_digitos(n) :
    while n < 0 :
        n = int(input())

    aux_n = n
    cont_digs = 0

    while aux_n == 0 :
        cont_digs == 1

    while aux_n > 0 :
        cont_digs += 1
        aux_n //= 10

    return cont_digs

num = int(input())
contador_digitos = cont_digitos(num)
print(f"El número {num} tiene {contador_digitos} dígito(s)")