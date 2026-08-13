"""Run the full bronze -> silver -> gold pipeline for the rail GTFS static feed."""
import sys

import build_gold
import fetch_gtfs_static
import load_bronze
import transform_silver
from config import RAIL_CATEGORY
from db import connect


def main(categories):
    con = connect()
    for cat in categories:
        print(f"\n=== {cat} ===")
        fetch_gtfs_static.fetch(cat)
        load_bronze.load(con, cat)
        transform_silver.transform(con, cat)
    build_gold.build(con)
    con.close()


if __name__ == "__main__":
    main(sys.argv[1:] or [RAIL_CATEGORY])
