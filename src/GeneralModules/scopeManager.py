from sys import getrecursionlimit
from typing import Any, Iterator, Optional, List, Self, Union, cast

class FrameInfo(tuple):
    __slots__ = ()
    def __new__(cls, depth: int, id: int, context: Any):
        return super().__new__(cls, (depth, id, context))
    @property
    def depth(self) -> int: 
        return self[0]
        
    @property
    def id(self) -> int: 
        return self[1]
        
    @property
    def context(self) -> Any: 
        return self[2]

class YieldItem(tuple):
    __slots__ = ()
    def __new__(cls, value: Any, context: Optional[Any] = None):
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
# 3. ENGINE: The Autonomous Heap Frame 
# ============================================================
class StackFrame:
    __slots__ = ("parent", "depth", "payload", "explicit_engine", "_engine", "_peek")

    def __init__(
        self, 
        parent: Optional[Self] = None, 
        payload: Any = None, 
        explicit_engine: Optional[Iterator[Any]] = None
    ) -> None:
        self.parent = parent
        self.depth = 0 if parent is None else parent.depth + 1
        
        self.payload = payload
        self.explicit_engine = explicit_engine
        self._peek: Union[YieldItem, object] = _EMPTY
        self._engine: Optional[Iterator[Any]] = None 

    def _ensure_engine(self) -> Iterator[Any]:
        """Helper that guarantees an iterator is built and returns it strictly typed."""
        if self._engine is not None:
            return self._engine
            
        if self.explicit_engine is not None:
            self._engine = self.explicit_engine
        elif isinstance(self.payload, (str, bytes)):
            self._engine = iter([self.payload])
        else:
            try:
                self._engine = iter(self.payload)
            except TypeError:
                self._engine = iter([self.payload])
                
        return self._engine

    def peek(self) -> YieldItem:
        engine = self._ensure_engine()
        
        if self._peek is _EMPTY:
            raw_item = next(engine)
            self._peek = YieldItem(value=raw_item, context=self.payload)
        return cast(YieldItem, self._peek)

    def __iter__(self) -> Self:
        self._ensure_engine()
        return self

    def __next__(self) -> YieldItem:
        engine = self._ensure_engine()
        
        if self._peek is not _EMPTY:
            val = self._peek
            self._peek = _EMPTY
            return cast(YieldItem, val)
        
        raw_item = next(engine)
        return YieldItem(value=raw_item, context=self.payload)

    def pop(self) -> "StackFrame":
        if self.parent is None:
            raise BottomOutError("Cannot ascend above the root context node.")
        return self.parent


# ============================================================
# 4. ORCHESTRATION: The Hybrid C-Pump VM Controller
# ============================================================
class UniversalStack:
    __slots__ = ["_active_cursor", "max_size", "_live_generator"]
    def __init__(self, root_payload: Any, max_size: Optional[int] = None) -> None:
        self.max_size = max_size if max_size is not None else getrecursionlimit()
        self._active_cursor: Optional[StackFrame] = StackFrame(parent=None, payload=root_payload)
        self._live_generator: Optional[Iterator[tuple[Any, FrameInfo]]] = None

    @property
    def current_node(self) -> Optional[StackFrame]:
        """Returns the active tracking frame at the top of the stack."""
        return self._active_cursor

    @property
    def depth(self) -> int:
        """Returns the current depth boundary location on the heap."""
        return 0 if self._active_cursor is None else self._active_cursor.depth

    def __iter__(self) -> Iterator[tuple[Any, FrameInfo]]:
        while self._active_cursor is not None:
            try:
                item = next(self._active_cursor)
                signal = FrameInfo(self._active_cursor.depth, id(self._active_cursor), item.context)
                yield item.value, signal
            except StopIteration:
                try:
                    self.pop_frame()
                except BottomOutError:
                    break

    def next(self) -> tuple[Any, FrameInfo]:
        if self._live_generator is None:
            self._live_generator = self.__iter__()
            
        try:
            return next(self._live_generator)
        except StopIteration:
            if self._active_cursor:
                self._live_generator = self.__iter__()
                return next(self._live_generator)
            raise StopIteration

    def push_frame(self, block_payload: Any, engine: Optional[Iterator[Any]] = None) -> None:
        if self._active_cursor is not None and self._active_cursor.depth >= self.max_size:
            raise StackMaxed(self._active_cursor.depth, self.max_size)

        self._active_cursor = StackFrame(
            parent=self._active_cursor, 
            payload=block_payload, 
            explicit_engine=engine
        )

    def pop_frame(self) -> None:
        if self._active_cursor is not None:
            # If popping above root, self._active_cursor naturally becomes None and terminates the loop
            try:
                self._active_cursor = self._active_cursor.pop()
            except BottomOutError:
                self._active_cursor = None
