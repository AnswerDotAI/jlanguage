"A Jupyter kernel for J, using kernmini's Python API."
import sys
from importlib.metadata import version
from fastcore.xdg import xdg_config_home
from .core import J, JError


class JShell:
    "Run J on a dedicated thread with J's required stack size."
    @classmethod
    async def start(cls):
        from kernmini import ThreadWorker
        self = cls()
        self.worker = await ThreadWorker.start(J, stack_size=64 << 20)
        self.j = await self.worker.call(lambda j:j)
        startup = xdg_config_home()/'jlang'/'startup.ijs'
        if startup.exists():
            try: await self.worker.call(lambda j:j.run(startup.read_text()))
            except JError as e: print(f'startup.ijs failed: {e}', file=sys.stderr)
        self.banner = (await self.worker.call(lambda j:j.run("9!:14 ''"))).strip()
        return self

    def kernel_info(self):
        return dict(implementation='jlang', implementation_version=version('jlanguage'), banner=f'J {self.banner}',
            language_info=dict(name='J', version=self.banner.split('/')[0].lstrip('j'), mimetype='text/x-j', file_extension='.ijs'))

    async def execute(self, code, silent=False, **kwargs):
        try: text = await self.worker.call(lambda j:j.run(code))
        except JError as e:
            text = str(e).rstrip()
            return dict(error=dict(ename='JError', evalue=text, traceback=[text]))
        return dict(streams=[dict(name='stdout', text=text)] if text and not silent else [])

    def interrupt(self): self.j.interrupt()

    async def shutdown(self):
        await self.worker.call(lambda j:j.close())
        await self.worker.shutdown()


def run_kernel(connection_file):
    "Serve a J kernel on the Jupyter connection in `connection_file`."
    from kernmini import run_kernel as run
    run(connection_file, JShell.start, own_process_group=True)


if __name__=='__main__': run_kernel(sys.argv[1])
