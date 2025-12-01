import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle

# 1. Cargar dataset
df = pd.read_csv("dataset_filtros_entrenamiento.csv")

X = df[["turbidez", "coliformes", "metales", "tds", "olor"]]
y = df["filtro"]

# 2. Entrenar IA
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    random_state=42
)
model.fit(X, y)

# 3. Evaluación rápida
score = model.score(X, y)
print(f"Accuracy del modelo: {score * 100:.2f}%")

# 4. Guardar modelo
with open("modelo_filtros.pkl", "wb") as f:
    pickle.dump(model, f)

print("Modelo IA guardado como modelo_filtros.pkl")
