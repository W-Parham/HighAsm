from collections import namedtuple
from dataclasses import dataclass
from typing import Any, Iterator, Optional, List, Self, Union,cast

class FrameInfo(tuple):
    __slots__ = ()
    def __new__(cls, depth: int, id: int, context: Any):
        return super().__new__(cls, (depth, id, context))
        
    @property
    def depth(self) -> int: return self[0]
    @property
    def id(self) -> int: return self[1]
    @property
    def context(self) -> Any: return self[2]


class YieldItem(tuple):
    __slots__ = ()
    def __new__(cls, value: Any, context: Optional[Any] = None):
        # Correctly pass the data as a single tuple sequence to the tuple constructor
        return super().__new__(cls, (value, context))
    @property
    def value(self) -> Any:
        return self[0]
    @property
    def context(self) -> Optional[Any]:
        return self[1]


class BottomOutError(StopIteration):
    pass

class StackMaxed(RecursionError):
    def __init__(self, depth: int, max_depth: int):
        super().__init__(f"Stack depth {depth} exceeded max {max_depth}")
        self.depth = depth
        self.max_depth = max_depth

_EMPTY = object()


# ============================================================
# 1. SPACE: Pure Topology Tree Structure
# ============================================================
class StructuralReference:
    # Base slots for the fundamental topology
    __slots__ = ("parent", "depth")

    def __init__(self, parent: Optional[Self] = None) -> None:
        self.parent = parent
        self.depth = 0 if parent is None else parent.depth + 1


# ============================================================
# 2. SPACE: Pure Topology Tree Structure
# ============================================================
class StructuralNode(StructuralReference):
    # Only declare slots unique to this subclass
    __slots__ = ("nType", "_children")

    def __init__(self, parent: Optional[Self] = None, nType: str = "StructuralNode") -> None:
        super().__init__(parent)
        self.nType = nType
        self._children: List[Self] = []
        
        if self.parent is not None and hasattr(self.parent, "_link_child"):
            self.parent._link_child(self)

    def _link_child(self, child: Self) -> None:
        self._children.append(child)
    
    def ascend(self) -> Self:
        if self.parent is None:
            raise BottomOutError(f"{type(self).__name__} is at the bottom of its tree.")
        return self.parent

    def __getitem__(self, index: int | slice) -> Union[Self, List[Self]]:
        return self._children[index]

    def __len__(self) -> int:
        return len(self._children)

    def __iter__(self) -> Iterator[Self]:
        return iter(self._children)


# ============================================================
# 3. SPACE: StackEngine
# ============================================================
class StackFrame(StructuralReference):
    # Only declare slots unique to the engine frame
    __slots__ = ("payload", "explicit_engine", "_engine", "_peek")

    def __init__(self, parent: Optional[Self] = None, payload: Any = None, explicit_engine: Optional[Iterator[Any]] = None) -> None:
        super().__init__(parent)
        
        self.payload = payload
        self.explicit_engine = explicit_engine
        self._peek: Union[YieldItem,object] = _EMPTY
        
        if self.explicit_engine is not None:
            self._engine = self.explicit_engine
        elif isinstance(self.payload, (str, bytes)):
            self._engine = iter([self.payload])
        else:
            try:
                self._engine = iter(self.payload)
            except TypeError:
                self._engine = iter([self.payload])

    def peek(self) -> YieldItem:
        # 1. Grab a local reference
        current = self._peek
        
        # 2. If it is the sentinel, populate the register with a valid YieldItem
        if isinstance(current, object):
            raw_item = next(self._engine)
            current = YieldItem(value=raw_item, context=self.payload)
            self._peek = current
            
        # 3. Explicitly hint or assert to the linter that 'current' is now strictly a YieldItem
        return cast(YieldItem, current)

    def __iter__(self) -> Self|None:
        # LAZY INITIALIZATION: Only build the iterator if it hasn't been built yet
        if self._engine is None:
            if self.explicit_engine is not None:
                self._engine = self.explicit_engine
            elif isinstance(self.payload, (str, bytes)):
                self._engine = iter([self.payload])
            else:
                try:
                    self._engine = iter(self.payload)
                except TypeError:
                    self._engine = iter([self.payload])                
        return self

    def __next__(self) -> YieldItem:
        # 1. Cold cache path
        if self._peek is _EMPTY:
            raw_item = next(self._engine)
            return YieldItem(value=raw_item, context=self.payload)
        # 2. Warm cache path
        val = self._peek
        self._peek = _EMPTY       
        return val # type: ignore

    def pop(self) -> "StackFrame":
        if self.parent is None:
            raise BottomOutError("Cannot ascend above the root context node.")
        return self.parent
    
    def __repr__(self) -> str:
        return f"stackNode({self.payload})"


# ============================================================
# 3. ORCHESTRATION: The Inherited Stack Engine
# ============================================================
class UniversalStack:
    __slots__ = ["_active_cursor", "max_size","_live_generator"]

    def __init__(self, root_payload: Any, max_size: Optional[int] = None) -> None:
        self.max_size = max_size
        self._active_cursor = StackFrame(parent=None, payload=root_payload)
        # Initialize it as None so it spins up lazily on the first call
        self._live_generator: Optional[Iterator[tuple[Any, FrameInfo]]] = None

    @property
    def current_node(self) -> StackFrame:
        return self._active_cursor

    @property
    def depth(self) -> int:
        return self._active_cursor.depth

    def __iter__(self) -> Iterator[tuple[Any, FrameInfo]]:
        while self._active_cursor:
            try:
                item = next(self._active_cursor)
                signal = FrameInfo(self._active_cursor.depth, id(self._active_cursor), item.context)
                yield item.value, signal
            except StopIteration:
                self.pop_frame()

    def next(self) -> tuple[Any, FrameInfo]:
        """Safely fetches the next item, auto-relaunching the generator if needed."""
        # 1. If it's the very first call, spin up the generator
        if self._live_generator is None:
            self._live_generator = self.__iter__()
            
        try:
            return next(self._live_generator)
        except StopIteration:
            # 2. If it errored out, check if we pushed new frames in the meantime
            if self._active_cursor:
                # Relaunch a fresh generator and pull the new item instantly!
                self._live_generator = self.__iter__()
                return next(self._live_generator)
            else:
                # 3. Everything is truly empty, pass the error up
                raise StopIteration

    def push_frame(self, block_payload: Any, engine: Optional[Iterator[Any]] = None) -> None:
        if self.max_size is not None and self._active_cursor.depth >= self.max_size:
            raise StackMaxed(self._active_cursor.depth, self.max_size)

        self._active_cursor = StackFrame(
            parent=self._active_cursor, 
            payload=block_payload, 
            explicit_engine=engine
        )

    def pop_frame(self) -> None:
        self._active_cursor = self._active_cursor.pop()
