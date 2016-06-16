from __future__ import absolute_import

from .timer import Timer

import pxul.os

from abc import ABCMeta, abstractmethod, abstractproperty
import copy


class AbstractBenchmarkRunner:
    """
    An instance of AbstractBenchmarkRunner manages the lifecycle of a
    benchmark. This involves:

    #. fetching the benchmark
    #. preparing the environment to run the benchmark
    #. launching a virtual cluster
    #. deploying onto the virtual cluster
    #. running the benchmark
    #. cleaning up the virtual cluster

    In addition, the time taken to accomplish various components is
    tracked.


    Intended usage for developers:

    .. python:

       bench = MyBenchmarkRunner()
       bench.fetch()
       bench.prepare()
       bench.launch()
       bench.deploy()
       bench.run()
       bench.clean()


    Intended usage for users:

    .. python:

       bench = MyBenchmarkRunner(times='times.txt')
       bench.bench(times=10)


    The resultant ``times.txt`` can then be processed to generate figures.
    """


    __metaclass__ = ABCMeta


    ################################################## fetch

    @abstractmethod
    def _fetch(self, prefix):
        """Fetch everything required to run the current benchmark.

        This may be a ``git clone``, or downloading a tarball and extracting it.

        After this method is called the :func:`path` attribute may be
        accessed to get the path to the root directory of the benchmark.

        :param prefix: the path to a directory into which the
        benchmark should be made available.
        :type prefix: :class:`str`

        :returns: the full path to the fetched benchmark
        :rtype: :class:`str`
        """

        raise NotImplementedError


    def fetch(self, prefix=None):
        """Fetch everything required to run the benchmark

        :param prefix: where to put the directory (default is current working directory)
        :type prefix: :class:`str`
        :returns: location of the benchmark
        :rtype: :class:`str`
        """

        self._log.append('fetch')
        with self._timer.measure('fetch'):
            path = self._fetch(prefix)

        self._path = path
        return self.path


    ################################################## prepare

    @abstractmethod
    def _prepare(self):
        """Prepare the benchmark to be run

        :returns: any environment variables that need to be set for the benchmark
        :rtype: :class:`dict` of :class:`str` -> :class:`str`
        """

        raise NotImplementedError


    def prepare(self):
        """Prepare the benchmark to be run
        """

        self._log.append('prepare')

        with self._timer.measure('prepare'):
            self._env = self._prepare()


    ################################################## launch

    @abstractmethod
    def _launch(self):
        """Start the virtual cluster
        """

        raise NotImplementedError


    def launch(self):
        """Start the prepared virtual cluster
        """

        self._log.append('launch')

        with pxul.os.env(**self._env), self._timer.measure('launch'):
            self._launch()


    ################################################## deploy

    @abstractmethod
    def _deploy(self):
        """Deploy onto the launched virtual cluster
        """

        raise NotImplementedError


    def deploy(self):
        """Deploy onto the launched virtual cluster
        """

        self._log.append('deploy')

        with pxul.os.env(**self._env), self._timer.measure('deploy'):
            self._deploy()


    ################################################## running

    @abstractmethod
    def _run(self):
        """Run the benchmark
        """

        raise NotImplementedError


    def run(self):
        """Run the benchmark
        """

        self._log.append('run')

        with pxul.os.env(**self._env), self._timer.measure('run'):
            self._run()


    ################################################## cleanup

    @abstractmethod
    def _clean(self):
        """Cleanup after a benchmark
        """

        raise NotImplementedError


    def clean(self):
        """Cleanup after a benchmark
        """

        self._log.append('clean')

        with pxul.os.env(**self._env), self._timer.measure('cleanup'):
            self._clean()


    ################################################## bench

    def bench(self, times=1):
        """Run the entire benchmark

        :param times: the number of times to run
        :type times: :class:`int` greater than zero
        """

        if times < 1:
            msg = 'Benchmarks cannot be run less than once, but given {}'\
                  .format(times)
            raise ValueError(msg)

        self._log.append('bench(times={})'.format(times))

        for i in xrange(times):
            self.fetch()
            self.prepare()
            self.launch()
            self.deploy()
            self.run()
            self.clean()
            


    ##################################################


    @property
    def _timer(self):
        """Get the timer for this benchmark

        :returns: the timer
        :rtype: :class:`Timer`
        """

        if not hasattr(self, '__timer'):
            self.__timer = Timer()
        return self.__timer


    @property
    def _log(self):
        """A log of the operations called

        :returns: the log
        :rtype: :class:`list` of :class:`str`
        """

        if not hasattr(self, '__log'):
            self.__log = list()
        return self.__log


    @property
    def path(self):
        """
        :returns: The path to benchmark directory
        :rtype: str
        """
        return self._path


    @property
    def env(self):
        """The environment for the benchmark as a dictionary from variable (:class:`str`) to value (:class:`str`).

        This is only available after :func:`prepare` has been called.
        """
        assert hasattr(self, '_env')
        return copy.deepcopy(self._env)
