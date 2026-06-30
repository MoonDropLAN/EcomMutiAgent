import json
import sqlite3

from app.domain.models import Product


class ProductService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def search(self, category: str | None = None, max_price: int | None = None) -> list[Product]:
        sql = "SELECT * FROM products WHERE 1=1"
        params: list[object] = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        if max_price is not None:
            sql += " AND base_price <= ?"
            params.append(max_price)
        sql += " ORDER BY student_scenario_score DESC, base_price ASC"

        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_to_product(row) for row in rows]

    def get_by_id(self, product_id: str) -> Product | None:
        row = self.conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return self._row_to_product(row) if row else None

    def _row_to_product(self, row: sqlite3.Row) -> Product:
        return Product(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            brand=row["brand"],
            base_price=row["base_price"],
            tags=json.loads(row["tags_json"]),
            specs=json.loads(row["specs_json"]),
            student_scenario_score=row["student_scenario_score"],
        )