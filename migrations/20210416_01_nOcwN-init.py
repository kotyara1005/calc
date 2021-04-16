"""
init
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        """
            create table state_tax (
                id serial primary key,
                state_code text unique not null,
                tax_rate decimal(12, 7) NOT NULL CONSTRAINT positive_tax_rate CHECK (tax_rate >= 0)
            );
            create table discount (
                id serial primary key,
                min_price decimal(12, 2) unique not null CONSTRAINT positive_min_price CHECK (min_price >= 0),
                discount decimal(12, 7) NOT NULL CONSTRAINT positive_discount CHECK (discount >= 0)
            );
        """,
        """
            drop table state_tax;
            drop table discount;
        """,
    )
]
