
import polars as pl
base = "experiments/data/"
# The document claims EPA hazard mammal oral LD50: 76 compounds
# But 08_epa_coverage shows epa_hazard herbicide mammal_oral_ld50 and natural_product mammal_oral_ld50
epa_cov = pl.read_csv(base+"epa_endpoint_coverage.csv")
epa_ld50 = epa_cov.filter((pl.col("source")=="epa_hazard") & (pl.col("endpoint")=="mammal_oral_ld50"))
print("EPA hazard mammal_oral_ld50:")
print(epa_ld50.select(["chemical_group","compounds_with_data"]))

# Also check the comparison.csv for the epa comparison
comp = pl.read_csv(base+"comparison.csv")
print("\nComparison rows for epa:")
print(comp.filter(pl.col("trait").str.contains("epa")).select(["trait","herbicide_median","natural_product_median","auc"]))
