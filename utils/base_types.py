from pydantic.dataclasses import dataclass


class _Base:
    def __iter__(self):
        for i in self.__annotations__:
            yield self.__getattribute__(i)

    def __getitem__(self, i):
        return tuple(self).__getitem__(i)


@dataclass(frozen=True)
class Quaternion(_Base):
    x: float
    y: float
    z: float
    w: float


@dataclass(frozen=True)
class Vector3(_Base):
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Vector2(_Base):
    x: float
    y: float
