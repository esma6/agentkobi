import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Uygulama açılışında bir kere yüklenir
orders_df      = pd.read_csv(DATA_DIR / "orders_full.csv")
products_df    = pd.read_csv(DATA_DIR / "products.csv")
critical_df    = pd.read_csv(DATA_DIR / "critical_stock.csv")
drafts_df      = pd.read_csv(DATA_DIR / "supplier_drafts_full.csv")