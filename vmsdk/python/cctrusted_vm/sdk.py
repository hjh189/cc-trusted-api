"""
The VMSDK implementation for ``CCTrusted`` API.
"""
import logging

# pylint: disable=unused-import
from cctrusted_base.api import CCTrustedApi
from cctrusted_base.imr import TcgIMR
from cctrusted_base.quote import Quote
from cctrusted_base.eventlog import TcgEventLog
from cctrusted_base.tcg import TcgAlgorithmRegistry
from cctrusted_vm.cvm import ConfidentialVM


LOG = logging.getLogger(__name__)

class CCTrustedVmSdk(CCTrustedApi):

    """CC trusted API implementation for a general CVM."""

    _inst = None

    @classmethod
    def inst(cls):
        """Singleton instance function."""
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        """Contrustor of CCTrustedCVM."""
        self._cvm = ConfidentialVM.inst()

    def get_default_algorithms(self) -> TcgAlgorithmRegistry:
        """Get the default Digest algorithms supported by trusted foundation.

        Different trusted foundation may support different algorithms, for example
        the Intel TDX use SHA384, TPM uses SHA256.

        Beyond the default digest algorithm, some trusted foundation like TPM
        may support multiple algorithms.

        Returns:
            The default algorithms.
        """
        return TcgAlgorithmRegistry(self._cvm.default_algo_id)

    def get_measurement_count(self) -> int:
        """Get the count of measurement register.

        Different trusted foundation may provide different count of measurement
        register. For example, Intel TDX TDREPORT provides the 4 measurement
        register by default. TPM provides 24 measurement (0~16 for SRTM and 17~24
        for DRTM).

        Beyond the real mesurement register, some SDK may extend virtual measurement
        reigster for addtional trust chain like container, namespace, cluster in
        cloud native paradiagm.

        Returns:
            The count of measurement registers
        """
        return len(self._cvm.imrs)

    def get_measurement(self, imr_select:[int, int]) -> TcgIMR:
        """Get measurement register according to given selected index and algorithms

        Each trusted foundation in CC environment provides the multiple measurement
        registers, the count is update to ``get_measurement_count()``. And for each
        measurement register, it may provides multiple digest for different algorithms.

        Args:
            imr_select ([int, int]): The first is index of measurement register,
                the second is the alrogithms ID

        Returns:
            The object of TcgIMR
        """
        imr_index = imr_select[0]
        algo_id = imr_select[1]

        if imr_index not in self._cvm.imrs:
            LOG.error("Invalid select index for IMR.")
            return None

        if algo_id is None or algo_id is TcgAlgorithmRegistry.TPM_ALG_ERROR:
            algo_id = self._cvm.default_algo_id

        return self._cvm.imrs[imr_index]

    def get_quote(
        self,
        nonce: bytearray = None,
        data: bytearray = None,
        extraArgs = None
    ) -> Quote:
        """Get the quote for given nonce and data.

        The quote is signing of attestation data (IMR values or hashes of IMR
        values), made by a trusted foundation (TPM) using a key trusted by the
        verifier.

        Different trusted foundation may use different quote format.

        Args:
            nonce (bytearray): against replay attacks.
            data (bytearray): user data
            extraArgs: for TPM, it will be given list of IMR/PCRs

        Returns:
            The ``Quote`` object.
        """
        return self._cvm.get_quote(nonce, data, extraArgs)

    def get_eventlog(self, start:int = None, count:int = None) -> TcgEventLog:
        """Get eventlog for given index and count.

        TCG log in Eventlog. Verify to spoof events in the TCG log, hence defeating
        remotely-attested measured-boot.
        To measure the full CC runtime environment, the eventlog may include addtional
        OS type and cloud native type event beyond the measured-boot.

        Returns:
            ``TcgEventLog`` object.
        """
        event_logs = TcgEventLog(self._cvm.cc_event_log)
        event_logs.select(start, count)

        return event_logs
