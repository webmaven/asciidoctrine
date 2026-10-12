# Ensure ES modules are served with a JavaScript MIME type.
#
# On Windows, Python's ``mimetypes`` has no registry entry for ``.mjs`` and falls
# back to ``text/plain``. Pyodide's ``module_test.html`` imports ``pyodide.mjs``
# as an ES module, and browsers refuse to execute a module served as
# ``text/plain`` -- so ``loadPyodide`` is never defined and every functional
# test errors during setup.
#
# On Linux, ``/etc/mime.types`` supplies ``text/javascript`` for ``.mjs``, which
# is why this only ever broke on Windows.
#
# pytest-pyodide serves ``dist/`` from a *separate* spawned process, so patching
# ``mimetypes`` from a test or conftest would not reach it. ``sitecustomize`` is
# imported at interpreter startup in that child, and ``PYTHONPATH`` is inherited
# across ``multiprocessing`` spawn -- which makes this the injection point that
# actually works. See ``dev.py functional`` / ``dev.ps1 functional``.
import mimetypes

mimetypes.add_type("text/javascript", ".mjs", strict=True)
