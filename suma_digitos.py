def sum_digs(n) :
    while n < 0 :
        n = int(input())

    suma = 0
    aux_n = n

    while n > 0 :
        dig = aux_n % 10
        suma += dig
        n //= 10

    return suma

num =int(input())
suma_digitos = sum_digs(num)
print(f"La suma de los dígitos de {num} es {suma_digitos}")