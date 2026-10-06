INF = float("inf")

class Table:

    def __init__(self, headers, rows):
        self.headers = [str(h) for h in headers]
        self.rows = [[self._cell(c) for c in row] for row in rows]

    @staticmethod
    def _cell(value):
        if value is None:
            return "-"
        if isinstance(value, float):
            if value == INF:
                return "-"
            if value.is_integer():
                return str(int(value))
            return "{:.2f}".format(value)
        return str(value)

    def render(self):
        widths = [len(h) for h in self.headers]
        for row in self.rows:
            for j, cell in enumerate(row):
                widths[j] = max(widths[j], len(cell))
        border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

        def row_line(cells):
            return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

        out = [border, row_line(self.headers), border]
        out.extend(row_line(r) for r in self.rows)
        out.append(border)
        return "\n".join(out)

class WeekPlan:

    def __init__(self, week, demand, previous, workforce,
                 hiring_cost, excess_cost, total_cost, cumulative_cost):
        self.week = week
        self.demand = demand
        self.previous = previous
        self.workforce = workforce
        self.hired = max(0, workforce - previous)
        self.fired = max(0, previous - workforce)
        self.hiring_cost = hiring_cost
        self.excess_cost = excess_cost
        self.total_cost = total_cost
        self.cumulative_cost = cumulative_cost


class WorkforceSizingModel:

    def __init__(self, demands, carry_rate=300, hiring_fixed=400,
                 hiring_per_worker=200, initial_workforce=0):
        if not demands:
            raise ValueError("Debe haber al menos una semana.")
        if initial_workforce < 0:
            raise ValueError("La fuerza inicial no puede ser negativa.")
        self.demands = list(demands)
        self.n_weeks = len(demands)
        self.carry_rate = carry_rate
        self.hiring_fixed = hiring_fixed
        self.hiring_per_worker = hiring_per_worker
        self.initial_workforce = initial_workforce
        self.max_workforce = max(max(demands), initial_workforce)

        self.cost_table = []        # cost_table[i][w]  = f_i(w)
        self.decision_table = []    # decision_table[i][w] = mejor w' anterior
        self.transition_tables = [] # matrices de transición por etapa
        self.workforce_levels = []  # ruta óptima w_0, w_1, ..., w_n
        self.plan = []              # lista de WeekPlan
        self.total_cost = None
        self.final_workforce = None
        self.solved = False

    def hiring_cost(self, previous, new):
        """Costo de pasar de `previous` a `new` trabajadores."""
        hired = new - previous
        if hired <= 0:
            return 0
        return self.hiring_fixed + self.hiring_per_worker * hired

    def excess_cost(self, week, workforce):
        excess = workforce - self.demands[week - 1]
        if excess <= 0:
            return 0
        return self.carry_rate * excess

    def solve(self):
        n = self.n_weeks
        w_max = self.max_workforce

        self.cost_table = [[INF] * (w_max + 1) for _ in range(n + 1)]
        self.decision_table = [[None] * (w_max + 1) for _ in range(n + 1)]
        self.transition_tables = [None] * (n + 1)
        self.cost_table[0][self.initial_workforce] = 0

        for week in range(1, n + 1):
            demand = self.demands[week - 1]
            trans = [[None] * (w_max + 1) for _ in range(w_max + 1)]
            for prev in range(w_max + 1):
                base = self.cost_table[week - 1][prev]
                if base == INF:
                    continue
                for new in range(w_max + 1):
                    if new < demand:          
                        continue
                    total = (base
                             + self.hiring_cost(prev, new)
                             + self.excess_cost(week, new))
                    trans[prev][new] = total
                    if total < self.cost_table[week][new]:
                        self.cost_table[week][new] = total
                        self.decision_table[week][new] = prev
            self.transition_tables[week] = trans

        self.final_workforce = min(
            range(w_max + 1), key=lambda w: self.cost_table[n][w])
        self.total_cost = self.cost_table[n][self.final_workforce]
        self._rebuild_path()
        self.solved = True
        return self.total_cost

    def _rebuild_path(self):
        """Backtracking: de la semana n hasta la semana 0."""
        n = self.n_weeks
        levels = [None] * (n + 1)
        levels[n] = self.final_workforce
        for week in range(n, 0, -1):
            prev = self.decision_table[week][levels[week]]
            if prev is None:
                raise RuntimeError("Estado inválido en la semana %d" % week)
            levels[week - 1] = prev
        self.workforce_levels = levels

        self.plan = []
        cumulative = 0
        for week in range(1, n + 1):
            prev, new = levels[week - 1], levels[week]
            h_cost = self.hiring_cost(prev, new)
            e_cost = self.excess_cost(week, new)
            total = h_cost + e_cost
            cumulative += total
            self.plan.append(WeekPlan(week, self.demands[week - 1], prev, new,
                                      h_cost, e_cost, total, cumulative))



def transition_table(model, week):
    headers = ["w' (anterior)"] + [str(w) for w in range(model.max_workforce + 1)]
    rows = []
    for prev in range(model.max_workforce + 1):
        row = [prev]
        for new in range(model.max_workforce + 1):
            row.append(model.transition_tables[week][prev][new])
        rows.append(row)
    return Table(headers, rows)


def stage_table(model, week):
    """Resumen de la etapa: f_i(w) y el mejor estado anterior."""
    headers = ["w (fuerza)", "Costo minimo f_i(w)", "Mejor w' (anterior)"]
    rows = []
    for w in range(model.max_workforce + 1):
        cost = model.cost_table[week][w]
        choice = model.decision_table[week][w]
        rows.append([w,
                     cost if cost != INF else None,
                     choice if choice is not None else None])
    return Table(headers, rows)


def dp_summary_table(model):
    headers = ["Etapa (i)"] + [str(w) for w in range(model.max_workforce + 1)]
    rows = []
    labels = {0: "0  (inicio)"}
    for i in range(1, model.n_weeks + 1):
        labels[i] = "%d (semana %d)" % (i, i)
    for i in range(model.n_weeks + 1):
        row = [labels[i]]
        for w in range(model.max_workforce + 1):
            cost = model.cost_table[i][w]
            row.append(cost if cost != INF else None)
        rows.append(row)
    return Table(headers, rows)


def decision_summary_table(model):
    headers = ["Etapa (i)"] + [str(w) for w in range(model.max_workforce + 1)]
    rows = []
    for i in range(1, model.n_weeks + 1):
        row = ["Semana %d" % i]
        for w in range(model.max_workforce + 1):
            row.append(model.decision_table[i][w])
        rows.append(row)
    return Table(headers, rows)


def path_table(model):
    headers = ["Paso", "Semana", "Fuerza optima w",
               "Costo acumulado f_i(w)", "Fuerza anterior w'"]
    rows = []
    for i in range(model.n_weeks, 0, -1):
        w = model.workforce_levels[i]
        rows.append(["backtracking", "semana %d" % i, w,
                     model.cost_table[i][w], model.workforce_levels[i - 1]])
    rows.append(["inicio", "antes de semana 1",
                 model.workforce_levels[0],
                 model.cost_table[0][model.workforce_levels[0]], "-"])
    return Table(headers, rows)


def plan_tables(model):
    dec_rows = []
    cost_rows = []
    tot_hired = tot_fired = tot_hire_cost = tot_excess_cost = 0
    for p in model.plan:
        dec_rows.append([p.week, p.demand, p.previous, p.workforce,
                         p.hired, p.fired])
        cost_rows.append([p.week, p.hiring_cost, p.excess_cost,
                          p.total_cost, p.cumulative_cost])
        tot_hired += p.hired
        tot_fired += p.fired
        tot_hire_cost += p.hiring_cost
        tot_excess_cost += p.excess_cost
    dec_rows.append(["TOTAL", "", "", "", tot_hired, tot_fired])
    cost_rows.append(["TOTAL", tot_hire_cost, tot_excess_cost,
                      model.total_cost, model.total_cost])

    t1 = Table(["Semana", "Demanda", "Fuerza anterior",
                "Fuerza optima", "Contratados", "Despedidos"], dec_rows)
    t2 = Table(["Semana", "Costo contratacion", "Costo excedente",
                "Costo semana", "Acumulado"], cost_rows)
    return t1, t2


def validate(model, expected):
    rows = []
    ok = True
    for i, exp in enumerate(expected["semanas"]):
        p = model.plan[i]
        got = {"contratados": p.hired, "despedidos": p.fired,
               "costo": p.total_cost}
        state = "OK" if got == exp else "ERROR"
        ok = ok and (got == exp)
        want = "contratar %d, despedir %d, costo $%d" % (
            exp["contratados"], exp["despedidos"], exp["costo"])
        have = "contratar %d, despedir %d, costo $%d" % (
            p.hired, p.fired, p.total_cost)
        rows.append([p.week, want, have, state])
    total_ok = model.total_cost == expected["total"]
    ok = ok and total_ok
    rows.append(["TOTAL", "costo $%d" % expected["total"],
                 "costo $%d" % model.total_cost,
                 "OK" if total_ok else "ERROR"])
    return ok, Table(["Semana", "Respuesta esperada", "Respuesta obtenida",
                      "Estado"], rows)

