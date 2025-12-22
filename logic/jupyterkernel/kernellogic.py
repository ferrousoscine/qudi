"""
IPython compatible kernel launcher module

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import time

import numpy as np
import pyqtgraph as pg
from qtpy import QtCore

from core.util.network import netobtain
from logic.generic_logic import GenericLogic

from .qzmqkernel import QZMQKernel

# -----------------------------------------------------------------------------
# The Qudi logic module
# -----------------------------------------------------------------------------


class QudiKernelLogic(GenericLogic):
    """Logic module providing a Jupyer-compatible kernel connected via ZMQ."""

    sigStartKernel = QtCore.Signal(str)
    sigStopKernel = QtCore.Signal(int)

    def __init__(self, **kwargs):
        """Create logic object
        @param dict kwargs: additional parameters as a dict
        """
        super().__init__(**kwargs)
        self.kernellist = dict()
        self.modules = set()

    def on_activate(self):
        """Prepare logic module for work."""
        self.kernellist = dict()
        self.modules = set()
        self._manager.sigModulesChanged.connect(self.updateModuleList)
        self.sigStartKernel.connect(self.updateModuleList, QtCore.Qt.QueuedConnection)

    def on_deactivate(self):
        """Deactivate module."""
        kernels = tuple(self.kernellist.keys())
        for k in kernels:
            self.stopKernel(k)

        i = 0
        while len(self.kernellist) > 0 and i < 100:
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
            i += 1

    def startKernel(self, config, external=None):
        """Start a qudi inprocess jupyter kernel.
        @param dict config: connection information for kernel
        @param callable external: function to call on exit of kernel

        @return str: uuid of the started kernel
        """
        realconfig = netobtain(config)
        self.log.debug(f"Start {realconfig}")
        kernel = QZMQKernel(realconfig)
        kernelthread = self._manager.tm.newThread(f"kernel-{kernel.engine_id}")
        kernel.moveToThread(kernelthread)
        kernel.user_global_ns.update(
            {"pg": pg, "np": np, "config": self._manager.tree["defined"], "manager": self._manager}
        )
        kernel.sigShutdownFinished.connect(self.cleanupKernel)
        self.log.debug(f"Kernel is {kernel.engine_id}")
        kernelthread.start()
        QtCore.QMetaObject.invokeMethod(
            kernel, "connect_kernel", QtCore.Qt.BlockingQueuedConnection
        )
        self.kernellist[kernel.engine_id] = kernel
        self.log.info(f"Finished starting Kernel {kernel.engine_id}")

        self.sigStartKernel.emit(kernel.engine_id)
        return kernel.engine_id

    def stopKernel(self, kernelid):
        """Tell kernel to close all sockets and stop hearteat thread.
        @param str kernelid: uuid of kernel to be stopped
        """
        realkernelid = netobtain(kernelid)
        self.log.info(f"Stopping kernel {realkernelid}")
        kernel = self.kernellist[realkernelid]
        QtCore.QMetaObject.invokeMethod(kernel, "shutdown")

    def cleanupKernel(self, kernelid, external=None):
        """Remove kernel reference and tell rpyc client for that kernel to exit.

        @param str kernelid: uuid of kernel reference to remove
        @param callable external: reference to rpyc client exit function
        """
        self.log.info(f"Cleanup kernel {kernelid}")
        self._manager.tm.quitThread(f"kernel-{kernelid}")
        del self.kernellist[kernelid]
        if external is not None:
            try:
                external.exit()
            except Exception:
                self.log.warning("External qudikernel starter did not exit")

    def updateModuleList(self):
        """Remove non-existing modules from namespace,
        add new modules to namespace, update reloaded modules
        """
        currentModules = set()
        newNamespace = dict()
        for base in ["hardware", "logic", "gui"]:
            for module in self._manager.tree["loaded"][base]:
                currentModules.add(module)
                newNamespace[module] = self._manager.tree["loaded"][base][module]
        discard = self.modules - currentModules
        for kernel in self.kernellist:
            self.kernellist[kernel].user_global_ns.update(newNamespace)
        for module in discard:
            for kernel in self.kernellist:
                self.kernellist[kernel].user_global_ns.pop(module, None)
        self.modules = currentModules
