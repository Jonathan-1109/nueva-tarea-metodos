from .table import *

class Report:

    ANCHO = 78

    def __init__(self):
        self._blocks = []

    def heading(self, text):
        self._blocks.append("=" * self.ANCHO)
        self._blocks.append(text.center(self.ANCHO))
        self._blocks.append("=" * self.ANCHO)

    def subheading(self, text):
        self._blocks.append("")
        self._blocks.append(text)
        self._blocks.append("-" * len(text))

    def line(self, text=""):
        self._blocks.append(str(text))

    def table(self, table_obj):
        self._blocks.append(table_obj.render())

    def text(self):
        return "\n".join(self._blocks)

    def show(self):
        print(self.text())

    def save(self, filename):
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(self.text())
            fh.write("\n")



def build_report(model):
    r = Report()
    r.heading("MODELO DE TAMAÑO DE LA FUERZA DE TRABAJO  -  PROGRAMACIÓN DINÁMICA")
    r.line("Programa main.py | POO | sin librerías externas")
    r.line()

    # ---------------------------- 1) Datos ------------------------------
    r.subheading("1) DATOS DEL PROBLEMA")
    rows = [[i + 1, b] for i, b in enumerate(model.demands)]
    r.table(Table(["Semana", "Demanda b_i (trabajadores)"], rows))
    r.line()
    r.line("Fuerza inicial ..................: %d trabajadores"
           % model.initial_workforce)
    r.line("Costo de excedente conservado ..: $%d por trabajador por semana"
           % model.carry_rate)
    r.line("Costo de nueva contratación ....: $%d (fijo) + $%d por trabajador"
           % (model.hiring_fixed, model.hiring_per_worker))
    r.line("Despido ........................: sin costo (sólo se paga el"
           " excedente conservado)")
    r.line("Estados (fuerza w) .............: 0 a %d trabajadores"
           % model.max_workforce)
    r.line("Restricción ....................: w >= b_i en cada semana")

    # --------------------- 2) Construcción paso a paso ------------------
    r.subheading("2) CONSTRUCCIÓN PASO A PASO DE LA TABLA DE PROGRAMACIÓN DINÁMICA")
    r.line("Recurrencia:  f_i(w) = min_w' { f_{i-1}(w') + costo_contratación(w',w)"
           " + costo_excedente(i,w) }")
    r.line("Celda vacía (-) = estado inalcanzable o demanda no satisfecha.")
    for week in range(1, model.n_weeks + 1):
        r.line()
        r.line("-------- ETAPA %d : SEMANA %d (demanda b_%d = %d) --------"
               % (week, week, week, model.demands[week - 1]))
        prev_vals = []
        for w in range(model.max_workforce + 1):
            c = model.cost_table[week - 1][w]
            prev_vals.append("%d:%s" % (w, "-" if c == INF else int(c)))
        r.line("f_%d(w') = [%s]" % (week - 1, ", ".join(prev_vals)))
        r.line("Matriz de transición (filas = w' anterior, columnas = w nueva,"
               " celda = costo total f_{i-1}+contratar+excedente):")
        r.table(transition_table(model, week))
        r.line("Resumen de la etapa (mínimo por cada estado w):")
        r.table(stage_table(model, week))

    # ------------------------- 3) Tabla DP final ------------------------
    r.subheading("3) TABLA DP RESUMEN  f_i(w)  (costo mínimo acumulado)")
    r.table(dp_summary_table(model))
    r.line("Celdas con (-): estado inalcanzable o no factible (w < b_i).")

    # ---------------------- 4) Tabla de decisiones ----------------------
    r.subheading("4) TABLA DE DECISIONES (mejor fuerza anterior w')")
    r.table(decision_summary_table(model))
    r.line("Permite saber de qué estado anterior proviene el mínimo f_i(w).")

    # ------------------ 5) Reconstrucción de la ruta óptima -------------
    r.subheading("5) RECONSTRUCCIÓN DE LA RUTA ÓPTIMA (backtracking)")
    r.line("Mejor fuerza final: w = %d  con costo mínimo f_%d(w) = $%d"
           % (model.final_workforce, model.n_weeks, model.total_cost))
    r.table(path_table(model))
    levels = model.workforce_levels
    r.line("Ruta óptima: " + " -> ".join(
        "w_%d=%d" % (i, levels[i]) for i in range(len(levels))))

    # ------------------------ 6) Plan óptimo ----------------------------
    r.subheading("6) PLAN ÓPTIMO SEMANA A SEMANA")
    t1, t2 = plan_tables(model)
    r.line("Decisiones de fuerza de trabajo:")
    r.table(t1)
    r.line("Costos semanales:")
    r.table(t2)
    r.line()
    r.line(">>> COSTO TOTAL DE MANO DE OBRA = $%d <<<" % model.total_cost)

    return r