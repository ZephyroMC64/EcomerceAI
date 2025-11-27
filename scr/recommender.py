import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class ProductRecommender:

    def __init__(self, productos):
        # Convertir productos a DataFrame
        self.df = pd.DataFrame([{
            "id": p.id,
            "nombre": p.nombre,
            "texto": f"{p.nombre} {p.descripcion}"
        } for p in productos])

        # Stopwords español
        stopwords_es = [
            "el", "la", "los", "las", "un", "una", "unos", "unas",
            "de", "del", "a", "y", "o", "que", "con", "para", "por",
            "su", "sus", "en", "al", "se"
        ]

        # Vectorizador
        self.vectorizer = TfidfVectorizer(
            stop_words=stopwords_es
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["texto"])
        self.sim_matrix = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)

    def recomendar(self, producto_id, top_n=5):
        filas = self.df[self.df["id"] == producto_id]
        if filas.empty:
            return []   # Producto no está en el DF → sin recomendación

        idx = filas.index[0]
        scores = list(enumerate(self.sim_matrix[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        indices = [i for i, score in scores[1:top_n+1]]
        return self.df.iloc[indices]["id"].tolist()
