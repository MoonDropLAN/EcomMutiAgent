import sqlite3


class InventoryService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_stock(self, product_id: str) -> dict[str, int]:
        row = self.conn.execute(
            "SELECT available_stock, locked_stock FROM inventory WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            return {"available_stock": 0, "locked_stock": 0}
        return {"available_stock": row["available_stock"], "locked_stock": row["locked_stock"]}

    def lock(self, product_id: str, quantity: int) -> bool:
        stock = self.get_stock(product_id)
        if stock["available_stock"] < quantity:
            return False
        self.conn.execute(
            """
            UPDATE inventory
            SET available_stock = available_stock - ?, locked_stock = locked_stock + ?
            WHERE product_id = ?
            """,
            (quantity, quantity, product_id),
        )
        self.conn.commit()
        return True

    def release(self, product_id: str, quantity: int) -> None:
        stock = self.get_stock(product_id)
        release_quantity = min(quantity, stock["locked_stock"])
        self.conn.execute(
            """
            UPDATE inventory
            SET available_stock = available_stock + ?, locked_stock = locked_stock - ?
            WHERE product_id = ?
            """,
            (release_quantity, release_quantity, product_id),
        )
        self.conn.commit()

    def consume_locked(self, product_id: str, quantity: int) -> None:
        stock = self.get_stock(product_id)
        if stock["locked_stock"] < quantity:
            raise ValueError(f"锁定库存不足: {product_id}")
        self.conn.execute(
            "UPDATE inventory SET locked_stock = locked_stock - ? WHERE product_id = ?",
            (quantity, product_id),
        )
        self.conn.commit()