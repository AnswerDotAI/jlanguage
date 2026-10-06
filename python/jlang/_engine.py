"J's C API through ctypes."
import ctypes as ct, math, os, threading
from collections import deque

_I, _P = ct.c_ssize_t, ct.c_void_p
_Callback = ct.WINFUNCTYPE if os.name=='nt' else ct.CFUNCTYPE


class JError(Exception):
    "A J error, including its output and error display."


def _ravel(value):
    if not isinstance(value, (list,tuple)): return [],[value]
    if not value: return [0],[]
    parts = [_ravel(item) for item in value]
    shape = parts[0][0]
    if any(dims!=shape for dims,_ in parts): raise JError('the shape must be rectangular')
    return [len(value), *shape],[item for _,items in parts for item in items]


class _J:
    "A J engine, used on the thread that created it."
    def __init__(self, lib):
        self.api = (ct.WinDLL if os.name=='nt' else ct.CDLL)(str(lib))
        signatures = dict(JInit2=(_P, [ct.c_char_p]), JSM=(None, [_P, ct.POINTER(_P)]),
            JDo=(ct.c_int, [_P, ct.c_char_p]), JFree=(ct.c_int, [_P]), JInterrupt=(None, [_P]),
            JGetM=(ct.c_int, [_P, ct.c_char_p, *[ct.POINTER(_I)]*4]),
            JSetM=(ct.c_int, [_P, ct.c_char_p, *[ct.POINTER(_I)]*4]))
        for name,(restype,argtypes) in signatures.items():
            fn = getattr(self.api, name)
            fn.restype,fn.argtypes = restype,argtypes
        self.thread,self.exited = threading.get_ident(),None
        self._output,self._input = output,lines = [],deque()
        self._exit = exit_code = [None]
        buffer = [None]

        @_Callback(None, _P, ct.c_int, _P)
        def write(jt, kind, text):
            if kind==5: exit_code[0] = _I(text or 0).value
            elif text: output.append((kind, ct.string_at(text).decode(errors='replace')))

        @_Callback(_P, _P, ct.c_char_p)
        def read(jt, prompt):
            buffer[0] = ct.create_string_buffer((lines.popleft() if lines else ')').encode())
            return ct.addressof(buffer[0])

        self._callbacks = write,read
        self.jt = self.api.JInit2(str(lib.parent).encode())
        if not self.jt: raise JError('J failed to start')
        slots = (_P*5)(ct.cast(write, _P), None, ct.cast(read, _P), None, 3)
        self.api.JSM(self.jt, slots)
        binpath = str(lib.parent).replace("'", "''")
        self.run(f"(3 : '0!:0 y')<BINPATH,'/profile.ijs'[ARGV_z_=:<'jconsole'[BINPATH_z_=:'{binpath}'")

    def _check_thread(self):
        if not self.jt: raise JError('the J session is closed')
        if threading.get_ident()!=self.thread: raise JError('a J session runs only on the thread that created it')

    def run(self, code):
        self._check_thread()
        if '\0' in code: raise JError('J code cannot contain NUL characters')
        self._output.clear()
        self._input.clear()
        self._input.extend(code.strip().splitlines())
        self._exit[0] = None
        while self._input and self.exited is None:
            failed = self.api.JDo(self.jt, self._input.popleft().encode())
            self.exited = self._exit[0]
            if failed and self.exited is None: raise JError(''.join(text for _,text in self._output))
        return ''.join(text for kind,text in self._output if self.exited is None or kind!=2)

    def get(self, name):
        self._check_thread()
        kind,rank,shape,at = (_I() for _ in range(4))
        if self.api.JGetM(self.jt, name.encode(), *map(ct.byref, (kind,rank,shape,at))): raise JError(f'no noun: {name}')
        shape = list((_I*rank.value).from_address(shape.value)) if rank.value else []
        n = math.prod(shape)
        if kind.value==2: data = ct.string_at(at.value, n).decode(errors='replace') if n else ''
        else:
            typ = {1:ct.c_ubyte, 4:_I, 8:ct.c_double}.get(kind.value)
            if typ is None: raise JError(f'unsupported J type {kind.value} for: {name}')
            data = list((typ*n).from_address(at.value)) if n else []
        return shape,data

    def set(self, name, items):
        self._check_thread()
        if isinstance(items,str):
            encoded = items.encode()
            shape,kind,data = [len(encoded)],_I(2),ct.create_string_buffer(encoded)
        else:
            shape,items = _ravel(items)
            typ = _I if all(isinstance(v,int) for v in items) else ct.c_double
            kind,data = _I(4 if typ is _I else 8),(typ*len(items))(*items)
        dims = (_I*len(shape))(*shape)
        rank,at_shape,at_data = _I(len(shape)),_I(ct.addressof(dims)),_I(ct.addressof(data))
        # JSetM returns the previous error flag; an empty sentence clears it.
        self.api.JDo(self.jt, b'')
        if self.api.JSetM(self.jt, name.encode(), *map(ct.byref, (kind,rank,at_shape,at_data))): raise JError(f'JSetM failed: {name}')

    def interrupt(self):
        if self.jt: self.api.JInterrupt(self.jt)

    def close(self):
        if getattr(self, 'jt', None):
            self.api.JFree(self.jt)
            self.jt = None

    def __del__(self): self.close()
