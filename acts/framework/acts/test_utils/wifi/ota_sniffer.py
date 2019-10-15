from acts import logger
from acts.controllers.utils_lib import ssh
import csv
import io
import os


def create(configs, logging_dir):
    """Factory method for sniffer
    Args:
        configs: list of dicts with sniffer settings, settings must contain the following :
        ssh_settings (ssh credentials required to log into the sniffer)
    """
    objs = []
    for config in configs:
        try:
            if config["type"] == "tshark":
                objs.append(TsharkSniffer(config, logging_dir))
            elif config["type"] == "mock":
                objs.append(MockSniffer(config, logging_dir))
        except KeyError:
            raise KeyError("Invalid sniffer configurations")
        return objs


def destroy(objs):
    return


class OtaSnifferBase(object):
    """Base class provides functions whose implementation in shared by all sniffers"""

    _log_file_counter = 0

    def start_capture(self):
        """Starts the sniffer Capture"""
        raise NotImplementedError

    def stop_capture(self):
        """Stops the sniffer Capture"""
        raise NotImplementedError

    def _get_remote_dump_path(self):
        return "sniffer_dump.csv"

    def _get_full_file_path(self, tag=None):
        """Returns the full file path for the sniffer capture dump file.

        Returns the full file path (on test machine) for the sniffer capture dump file

        Args:
            tag: The tag appended to the sniffer capture dump file .
        """
        out_dir = os.path.join(self.log_dir, "sniffer_files")
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        tags = [tag, "count", OtaSnifferBase._log_file_counter]
        out_file_name = 'Sniffer_Capture_%s.csv' % ('_'.join(
            [str(x) for x in tags if x != '' and x is not None]))
        OtaSnifferBase._log_file_counter += 1

        file_path = os.path.join(out_dir, out_file_name)
        return file_path


class MockSniffer(OtaSnifferBase):
    """Class that implements mock sniffer for test development and debug"""

    def __init__(self, config, logging_dir):
        self.log = logger.create_tagged_trace_logger("Mock Sniffer")
        self.log_dir = logging_dir

    def _ssh_into_sniffer(self):
        """logs into the sniffer machine"""
        self.log.info("Logging into the sniffer machine")

    def _connect_to_network(self):
        """ Connects to a given network

        Args:
            network: dictionary of network credentials; SSID and password
        """
        self.log.info("Connecting to wireless network ")

    def _run_sniffer(self):
        """Starts the sniffer"""
        self.log.info("Starting Sniffer")
        self.log.info(
            "Executing sniffer command on the sniffer machine")

    def _stop_sniffer(self):
        """ Stops the sniffer"""
        self.log.info("Stopping Sniffer")

    def start_capture(self):
        """Starts sniffer capture on the specified machine"""

        self._ssh_into_sniffer()
        self._connect_to_network()
        self._run_sniffer()

    def stop_capture(self):
        """Stops the sniffer

        Returns:
            The name of the processed sniffer dump from the terminated sniffer process
        """

        self._stop_sniffer()
        log_file = self._get_full_file_path("Mock")
        return log_file


class TsharkSniffer(OtaSnifferBase):
    """Class that implements Tshark based Sniffer """

    def __init__(self, config, logging_dir):
        self.sniffer_proc_pid = None
        self.log = logger.create_tagged_trace_logger("Tshark Sniffer")
        self.ssh_config = config["ssh_config"]
        self.params = config["sniffer_params"]
        self.log_dir = logging_dir
        self.type_subtype_dict = {
            "0": "Association Requests",
            "1": "Association Responses",
            "2": "Reassociation Requests",
            "3": "Resssociation Responses",
            "4": "Probe Requests",
            "5": "Probe Responses",
            "8": "Beacon",
            "9": "ATIM",
            "10": "Disassociations",
            "11": "Authentications",
            "12": "Deauthentications",
            "13": "Actions",
            "24": "Block ACK Requests",
            "25": "Block ACKs",
            "26": "PS-Polls",
            "27": "RTS",
            "28": "CTS",
            "29": "ACK",
            "30": "CF-Ends",
            "31": "CF-Ends/CF-Acks",
            "32": "Data",
            "33": "Data+CF-Ack",
            "34": "Data+CF-Poll",
            "35": "Data+CF-Ack+CF-Poll",
            "36": "Null",
            "37": "CF-Ack",
            "38": "CF-Poll",
            "39": "CF-Ack+CF-Poll",
            "40": "QoS Data",
            "41": "QoS Data+CF-Ack",
            "42": "QoS Data+CF-Poll",
            "43": "QoS Data+CF-Ack+CF-Poll",
            "44": "QoS Null",
            "46": "QoS CF-Poll (Null)",
            "47": "QoS CF-Ack+CF-Poll (Null)"
        }

        self.tshark_columns = [
            "frame_number", "frame_time_relative", "mactime", "frame_len",
            "rssi", "channel", "ta", "ra", "bssid", "type", "subtype",
            "duration", "seq", "retry", "pwrmgmt", "moredata", "ds", "phy",
            "radio_datarate", "vht_datarate", "radiotap_mcs_index", "vht_mcs", "wlan_data_rate",
            "11n_mcs_index", "11ac_mcs", "11n_bw", "11ac_bw", "vht_nss", "mcs_gi",
            "vht_gi", "vht_coding", "ba_bm", "fc_status",
            "bf_report"
        ]


        self._tshark_output_columns = [
            "frame_number",
            "frame_time_relative",
            "mactime",
            "ta",
            "ra",
            "bssid",
            "rssi",
            "channel",
            "frame_len",
            "Info",
            "radio_datarate",
            "radiotap_mcs_index",
            "pwrmgmt",
            "phy",
            "vht_nss",
            "vht_mcs",
            "vht_datarate",
            "11ac_mcs",
            "11ac_bw",
            "vht_gi",
            "vht_coding",
            "wlan_data_rate",
            "11n_mcs_index",
            "11n_bw",
            "mcs_gi",
            "type",
            "subtype",
            "duration",
            "seq",
            "retry",
            "moredata",
            "ds",
            "ba_bm",
            "fc_status",
            "bf_report"
        ]


        self.tshark_fields = '-T fields -e frame.number -e frame.time_relative -e radiotap.mactime -e frame.len '+\
        '-e radiotap.dbm_antsignal -e wlan_radio.channel '+\
        '-e wlan.ta -e wlan.ra -e wlan.bssid '+\
        '-e wlan.fc.type -e wlan.fc.type_subtype -e wlan.duration -e wlan.seq -e wlan.fc.retry -e wlan.fc.pwrmgt -e wlan.fc.moredata -e wlan.fc.ds '+\
        '-e wlan_radio.phy '+\
        '-e radiotap.datarate -e radiotap.vht.datarate.0 '+\
        '-e radiotap.mcs.index -e radiotap.vht.mcs.0 '+\
        '-e wlan_radio.data_rate -e wlan_radio.11n.mcs_index -e wlan_radio.11ac.mcs '+\
        '-e wlan_radio.11n.bandwidth -e wlan_radio.11ac.bandwidth '+\
        '-e radiotap.vht.nss.0 -e radiotap.mcs.gi -e radiotap.vht.gi -e radiotap.vht.coding.0 '+\
        '-e wlan.ba.bm -e wlan.fcs.status -e wlan.vht.compressed_beamforming_report.snr '+ \
        '-y IEEE802_11_RADIO -E separator="^" '

    @property
    def _started(self):
        return self.sniffer_proc_pid is not None

    def _ssh_into_sniffer(self):
        """logs into the sniffer machine"""
        self.log.info("Logging into Sniffer")
        self._sniffer_server = ssh.connection.SshConnection(
            ssh.settings.from_config(self.ssh_config))

    def _connect_to_network(self, network):
        """ Connects to a given network
        Connects to a wireless network using networksetup utility

        Args:
            network: dictionary of network credentials; SSID and password
        """
        self.log.info("Connecting to network {}".format(network["SSID"]))

        #Scan to see if the requested SSID is available
        scan_result = self._sniffer_server.run("/usr/local/bin/airport -s")

        if network["SSID"] not in scan_result.stdout:
            self.log.error("{} not found in scan".format(network["SSID"]))

        if "password" not in network.keys():
            network["password"] = ""

        if set(["SSID", "password"]).issubset(network.keys()):
            pass
        else:
            raise KeyError("Incorrect Network Config")

        connect_command = "networksetup -setairportnetwork en0 {} {}".format(
            network["SSID"], network["password"])
        self._sniffer_server.run(connect_command)

    def _run_tshark(self, sniffer_command):
        """Starts the sniffer"""

        self.log.info("Starting Sniffer")
        sniffer_job = self._sniffer_server.run_async(sniffer_command)
        self.sniffer_proc_pid = sniffer_job.stdout

    def _stop_tshark(self):
        """ Stops the sniffer"""

        self.log.info("Stopping Sniffer")

        # while loop to kill the sniffer process
        while True:
            try:
                #Returns error if process was killed already
                self._sniffer_server.run("kill -15 {}".format(
                    str(self.sniffer_proc_pid)))
            except:
                pass
            try:
                #Returns 1 if process was killed
                self._sniffer_server.run(
                    "/bin/ps aux| grep {} | grep -v grep".format(
                        self.sniffer_proc_pid))
            except:
                break

    def _process_tshark_dump(self, dump, sniffer_tag):
        """ Process tshark dump for better readability
        Processes tshark dump for better readability and saves it to a file.
        Adds an info column at the end of each row.
        Format of the info columns: subtype of the frame, sequence no and retry status

        Args:
            dump : string of sniffer capture output
            sniffer_tag : tag to be appended to the dump file

        Returns:
            log_file : name of the file where the processed dump is stored
        """
        dump = io.StringIO(dump)
        log_file = self._get_full_file_path(sniffer_tag)
        with open(log_file, "w") as output_csv:
            reader = csv.DictReader(
                dump, fieldnames=self.tshark_columns, delimiter="^")
            writer = csv.DictWriter(
                output_csv, fieldnames=self._tshark_output_columns, delimiter="\t")
            writer.writeheader()
            for row in reader:
                if row["subtype"] in self.type_subtype_dict.keys():
                    row["Info"] = "{sub} S={seq} retry={retry_status}".format(
                        sub=self.type_subtype_dict[row["subtype"]],
                        seq=row["seq"],
                        retry_status=row["retry"])
                else:
                    row["Info"] = "{sub} S={seq} retry={retry_status}\n".format(
                        sub=row["subtype"],
                        seq=row["seq"],
                        retry_status=row["retry"])
                writer.writerow(row)
        return log_file

    def start_capture(self, network, duration=30):
        """Starts sniffer capture on the specified machine"""

        # Checking for existing sniffer processes
        if self._started:
            self.log.info("Sniffer already running")
            return

        self.tshark_command = "/usr/local/bin/tshark -l -I -t u -a duration:{}".format(
            duration)

        # Logging into the sniffer
        self._ssh_into_sniffer()

        #Connecting to network
        self._connect_to_network(network)

        sniffer_command = "{tshark} {fields} > {log_file}".format(
            tshark=self.tshark_command,
            fields=self.tshark_fields,
            log_file=self._get_remote_dump_path())

        #Starting sniffer capture by executing tshark command
        self._run_tshark(sniffer_command)

    def stop_capture(self, sniffer_tag=""):
        """Stops the sniffer

        Returns:
            The name of the processed sniffer dump from the terminated sniffer process
        """
        #Checking if there is an ongoing sniffer capture
        if not self._started:
            self.log.error("No sniffer process running")
            return
        # Killing sniffer process
        self._stop_tshark()

        sniffer_dump = self._sniffer_server.run('cat {}'.format(
            self._get_remote_dump_path()))

        #Processing writing capture output to file
        log_file = self._process_tshark_dump(sniffer_dump.stdout, sniffer_tag)

        self.sniffer_proc_pid = None

        return log_file
