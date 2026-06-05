from __future__ import annotations

import typing

import pydantic

_Item = typing.TypeVar("_Item")


class ListResponse(pydantic.RootModel[list[_Item]]):
    """Base class for array response schemas. Provides list-like access to the root list."""

    def __len__(self) -> int:
        return len(self.root)

    def __getitem__(self, index: int) -> _Item:
        return self.root[index]

    def __iter__(self) -> typing.Iterator[_Item]:  # ty: ignore[invalid-method-override]
        return iter(self.root)
