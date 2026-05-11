import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent

# Uygulama acilisinda bir kere yuklenir
orders_df = pd.read_csv(DATA_DIR / "orders_full.csv")
orders_by_business_df = pd.read_csv(DATA_DIR / "orders.csv")
products_df = pd.read_csv(DATA_DIR / "products.csv")
critical_df = pd.read_csv(DATA_DIR / "critical_stock.csv")
drafts_df = pd.read_csv(DATA_DIR / "supplier_drafts_full.csv")
drafts_by_business_df = pd.read_csv(DATA_DIR / "supplier_drafts.csv")
customers_df = pd.read_csv(DATA_DIR / "customers.csv")