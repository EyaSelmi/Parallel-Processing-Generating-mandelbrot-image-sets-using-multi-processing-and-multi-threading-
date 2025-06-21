# Mandelbrot Parallel Series

Ce projet Python illustre différentes techniques de **programmation parallèle et concurrente** en générant des images de l'ensemble de **Mandelbrot**.

Il comprend des implémentations utilisant :

- ✅ Exécution séquentielle
- ✅ Multithreading (threads)
- ✅ Multiprocessing (processus)
- ✅ Synchronisation par modèles classiques :
    - 🧵 Producteurs / Consommateurs
    - 🪑 Sleeping Barber
    - 🍴 Dining Philosophers

## 📁 Structure des fichiers

| Fichier                                | Description                                                                 |
|----------------------------------------|-----------------------------------------------------------------------------|
| `mandel.py`                            | Fonctions de base pour calcul Mandelbrot (`iterations_at_point`, couleurs) |
| `mandelseries.py`                      | Version séquentielle                                                       |
| `mandelseries_sync.py`                | Producteurs / consommateurs avec threading et multiprocessing              |
| `mandelseries_sleeping_barber.py`     | Version utilisant le modèle du "Sleeping Barber" (file bornée, conditions) |
| `mandelseries_philosophers.py`        | Version utilisant le modèle des "Dining Philosophers"                      |
| `bitmap_loader.py` *(optionnel)*      | Chargement manuel de fichiers BMP (si utilisé)                             |
| `README.md`                            | Ce fichier                                                                 |

## ▶️ Exécution

### Séquentiel
```bash
python mandelseries.py -m 1000 -x -0.5 -y 0 -s 1.5 -W 800 -H 600 -o mandel_seq.png

Multithreading
python mandelseries.py 4 mt
Multiprocessing

python mandelseries.py 4 mp
Philosophe synchronisé

python mandelseries_philosophers.py
Barber synchronisé (threads + processus)

python mandelseries_sleeping_barber.py
Producteur / Consommateur synchronisé

python mandelseries_sync.py