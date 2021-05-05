from enum import Enum, unique


@unique
class SameSiteEnum(Enum):
    strict: str = "strict"
    lax: str = "lax"
    none: str = "none"
