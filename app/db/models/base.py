from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase):
    """Shared declarative base. All ORM models inherit from this.
    """

    pass
