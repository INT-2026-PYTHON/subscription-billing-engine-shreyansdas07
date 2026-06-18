def get(self, invoice_id: int) -> Optional[Invoice]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_id,)).fetchone()
            if not row:
                return None
            
            # Fetch line items to completely populate the Invoice domain model
            line_rows = conn.execute("SELECT * FROM invoice_line_items WHERE invoice_id = ?;", (invoice_id,)).fetchall()
            line_items = [
                InvoiceLineItem(
                    id=l_row["id"],
                    invoice_id=l_row["invoice_id"],
                    kind=LineItemKind(l_row["kind"]),
                    amount=Money.from_storage(l_row["amount"], row["currency"]),
                    description=l_row["description"]
                ) for l_row in line_rows
            ]

            return Invoice(
                id=row["id"],
                subscription_id=row["subscription_id"],
                customer_id=row["customer_id"],
                status=InvoiceStatus(row["status"]),
                period_start=date.fromisoformat(row["period_start"]),
                period_end=date.fromisoformat(row["period_end"]),
                subtotal=Money.from_storage(row["subtotal"], row["currency"]),
                discount_total=Money.from_storage(row["discount_total"], row["currency"]),
                tax_total=Money.from_storage(row["tax_total"], row["currency"]),
                total_amount=Money.from_storage(row["total_amount"], row["currency"]),
                pdf_path=row["pdf_path"],
                line_items=line_items
            )

    def count_for_subscription(self, subscription_id: int) -> int:
        """Used by FirstMonthFree discount."""
        with self.db.connect() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM invoices WHERE subscription_id = ?;", (subscription_id,)).fetchone()
            return row["count"]

    def mark_paid(self, invoice_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute("UPDATE invoices SET status = ? WHERE id = ?;", (InvoiceStatus.PAID.value, invoice_id))
            conn.commit()

    def mark_failed(self, invoice_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute("UPDATE invoices SET status = ? WHERE id = ?;", (InvoiceStatus.FAILED.value, invoice_id))
            conn.commit()

    def set_pdf_path(self, invoice_id: int, path: str) -> None:
        with self.db.connect() as conn:
            conn.execute("UPDATE invoices SET pdf_path = ? WHERE id = ?;", (path, invoice_id))
            conn.commit()


class InvoiceLineItemRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, line_item: InvoiceLineItem) -> InvoiceLineItem:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoice_line_items (invoice_id, kind, amount, description)
                VALUES (?, ?, ?, ?);
                """,
                (
                    line_item.invoice_id,
                    line_item.kind.value if hasattr(line_item.kind, "value") else str(line_item.kind),
                    line_item.amount.to_storage(),
                    line_item.description
                )
            )
            line_item.id = cursor.lastrowid
            conn.commit()
        return line_item

    def list_for_invoice(self, invoice_id: int) -> list[InvoiceLineItem]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM invoice_line_items WHERE invoice_id = ?;", (invoice_id,)).fetchall()
            return [
                InvoiceLineItem(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    kind=LineItemKind(row["kind"]),
                    amount=Money.from_storage(row["amount"], "USD"), # Falls back to standard evaluation context currency
                    description=row["description"]
                ) for row in rows
            ]


# ============================================================
# LEDGER — APPEND-ONLY (do not implement update/delete)
# ============================================================
class LedgerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ledger_entries (invoice_id, customer_id, amount, currency, direction, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    entry.invoice_id,
                    entry.customer_id,
                    entry.amount.to_storage(),
                    entry.currency,
                    entry.direction.value if hasattr(entry.direction, "value") else str(entry.direction),
                    entry.reason,
                    datetime.utcnow().isoformat()
                )
            )
            entry.id = cursor.lastrowid
            conn.commit()
        return entry

    def list_for_customer(self, customer_id: int) -> list[LedgerEntry]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM ledger_entries WHERE customer_id = ? ORDER BY id;", (customer_id,)).fetchall()
            return [
                LedgerEntry(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    customer_id=row["customer_id"],
                    amount=Money.from_storage(row["amount"], row["currency"]),
                    currency=row["currency"],
                    direction=LedgerDirection(row["direction"]),
                    reason=row["reason"]
                ) for row in rows
            ]

    def update(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")


# ============================================================
# PAYMENT ATTEMPTS
# ============================================================
class PaymentAttemptRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(
        self,
        invoice_id: int,
        attempt_no: int,
        status: str,
        failure_reason: Optional[str],
        next_retry_at: Optional[datetime],
    ) -> int:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO payment_attempts (invoice_id, attempt_no, status, failure_reason, next_retry_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    invoice_id,
                    attempt_no,
                    status,
                    failure_reason,
                    next_retry_at.isoformat() if next_retry_at else None,
                    datetime.utcnow().isoformat()
                )
            )
            new_id = cursor.lastrowid
            conn.commit()
        return new_id

    def list_for_invoice(self, invoice_id: int) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM payment_attempts WHERE invoice_id = ? ORDER BY attempt_no;", (invoice_id,)).fetchall()
            return [dict(row) for row in rows]

    def count_for_invoice(self, invoice_id: int) -> int:
        with self.db.connect() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM payment_attempts WHERE invoice_id = ?;", (invoice_id,)).fetchone()
            return row["count"]