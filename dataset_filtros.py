import numpy as np
import pandas as pd

np.random.seed(42)

# --------------------------
# Rangos realistas (basado en NOM-127 y estudios 2020-2024)
# --------------------------
N = 1200  # muestras para entrenar IA

turbidez = np.random.uniform(0.1, 50, N)
coliformes = np.random.uniform(0, 2000, N)
metales = np.random.uniform(0.0, 2.0, N)
tds = np.random.uniform(50, 1500, N)
olor = np.random.choice([0, 1], N)   # 0=no, 1=sí

df = pd.DataFrame({
    "turbidez": turbidez,
    "coliformes": coliformes,
    "metales": metales,
    "tds": tds,
    "olor": olor
})

# --------------------------
# Lógica experta → etiqueta (filtro correcto)
# --------------------------
def asignar_filtro(row):
    t, c, m, s, o = row

    # Ósmosis inversa → TDS alto, metales altos
    if s > 700 or m > 1.0:
        return "Ósmosis inversa"

    # Carbón activado → olor, sabor, orgánicos
    if o == 1 and t < 15:
        return "Carbón activado"

    # Zeolita → turbidez leve + metales medianos
    if t < 25 and 0.2 < m < 0.8:
        return "Zeolita"

    # Nano-fibras → alta carga biológica
    if c > 800:
        return "Nano-fibras"

    # Ultrafiltración → generalista para turbidez alta
    if t > 20:
        return "Ultrafiltración"

    # Si nada coincide → filtro más seguro
    return "Ósmosis inversa"

df["filtro"] = df.apply(asignar_filtro, axis=1)

# --------------------------
# Guardar dataset
# --------------------------
df.to_csv("dataset_filtros_entrenamiento.csv", index=False)
print("Dataset generado: dataset_filtros_entrenamiento.csv")
