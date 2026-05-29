def es_instruccion(texto) :
    return texto == "FIN" or texto == "AGREGAR" or texto == "INSERTAR" or texto == "ELIMINAR"
    
def imprimir_reporte(ventas) :
    
    total = sum(ventas)
    promedio = total / len(ventas)
    cont_0 = ventas.count(0)
    
    max_venta = max(ventas)
    pos_max = ventas.index(max_venta) + 1
    
    print(f"""Estadísticas
============
Total de ventas = {total}
Promedio de ventas de cafés por día = {promedio}
Cantidad de días con ventas = 0 es: {cont_0}
Mayor venta fue {max_venta} en día {pos_max}""")
    
cant_dias = int(input())

ventas = []

for i in range(cant_dias) :
    ventas.append(int(input()))

print(f"Lista inicial de ventas de cafés es: {ventas}")

    
instruccion = input()
    
print()
while instruccion != "FIN" :
    if instruccion == "AGREGAR" :
        x = int(input())
            
        ventas.append(x)
            
        print(f"AGREGAR {x} - nueva lista: {ventas}")
            
    elif instruccion == "INSERTAR" :
        pos = int(input())
        x = int(input())
            
        ventas.insert(pos, x)
            
        print(f"INSERTAR {pos} {x} - nueva lista: {ventas}")
            
    elif instruccion == "ELIMINAR" :
        x = int(input())
        if x in ventas : 
            ventas.remove(x)
            print(f"ELIMINAR {x} - nueva lista: {ventas}")
        else :
            print(f"ELIMINAR - {x} no está en la lista")
            
    instruccion = input()
print()

imprimir_reporte(ventas)