from core.report import *

ARCHIVO_SALIDA = "salida.txt"

def main():
    demandas = [5, 7, 8, 4, 6]

    esperado = {
        "total": 3300,
        "semanas": [
            {"contratados": 5, "despedidos": 0, "costo": 1400},
            {"contratados": 3, "despedidos": 0, "costo": 1300},
            {"contratados": 0, "despedidos": 0, "costo": 0},
            {"contratados": 0, "despedidos": 2, "costo": 600},
            {"contratados": 0, "despedidos": 0, "costo": 0},
        ],
    }

    modelo = WorkforceSizingModel(
        demands=demandas,
        carry_rate=300,          
        hiring_fixed=400,       
        hiring_per_worker=200,
        initial_workforce=0,
    )
    modelo.solve()

    reporte = build_report(modelo, esperado)
    reporte.show()
    reporte.save(ARCHIVO_SALIDA)

    print()
    print("Salida también guardada en el archivo: %s" % ARCHIVO_SALIDA)
    print("Costo total óptimo: $%d" % modelo.total_cost)


if __name__ == "__main__":
    main()
