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


class DictResponse(pydantic.RootModel[dict[str, _Item]]):
    """Base class for map schemas (additionalProperties). Provides dict-like access to the root dict."""

    def __len__(self) -> int:
        return len(self.root)

    def __getitem__(self, key: str) -> _Item:
        return self.root[key]

    def __iter__(self) -> typing.Iterator[str]:  # ty: ignore[invalid-method-override]
        return iter(self.root)

    def __contains__(self, key: str) -> bool:
        return key in self.root

    def get(self, key: str, default: typing.Optional[_Item] = None) -> typing.Optional[_Item]:
        return self.root.get(key, default)

    def keys(self) -> typing.KeysView[str]:
        return self.root.keys()

    def values(self) -> typing.ValuesView[_Item]:
        return self.root.values()

    def items(self) -> typing.ItemsView[str, _Item]:
        return self.root.items()
