from acts import asserts
from acts import base_test
from acts.controllers import android_device

from scapy.all import *
from threading import Event
from threading import Thread
import time
import warnings


SERVER_PORT = 67
BROADCAST_MAC = 'ff:ff:ff:ff:ff:ff'
NETADDR_PREFIX = '192.168.42.'
OTHER_NETADDR_PREFIX = '192.168.43.'
NETADDR_BROADCAST = '255.255.255.255'
SUBNET_BROADCAST = NETADDR_PREFIX + '255'


OFFER = 2
REQUEST = 3
ACK = 5
NAK = 6

pmc_base_cmd = (
    "am broadcast -a com.android.pmc.action.AUTOPOWER --es PowerAction ")
start_pmc_cmd = (
    "am start -S -n com.android.pmc/com.android.pmc.PMCMainActivity")
pmc_start_usb_tethering_cmd = "%sStartUSBTethering" % pmc_base_cmd
pmc_stop_usb_tethering_cmd = "%sStopUSBTethering" % pmc_base_cmd


class DhcpServerTest(base_test.BaseTestClass):
    def setup_class(self):
        self.dut = self.android_devices[0]
        self.USB_TETHERED = False
        self.next_hwaddr_index = 0
        self.stop_arp = Event()

        conf.checkIPaddr = 0
        conf.checkIPsrc = 0
        # Allow using non-67 server ports as long as client uses 68
        bind_layers(UDP, BOOTP, dport=68)

        self.dut.adb.shell(start_pmc_cmd)
        self.dut.adb.shell("setprop log.tag.PMC VERBOSE")
        iflist_before = get_if_list()
        self._start_usb_tethering(self.dut)
        self.iface = self._wait_for_new_iface(iflist_before)
        self.real_hwaddr = get_if_raw_hwaddr(self.iface)

        # Start a thread to answer to all ARP "who-has"
        thread = Thread(target=self._sniff_arp, args=(self.stop_arp,))
        thread.start()

        # Discover server IP
        hwaddr = self._next_hwaddr()
        resp = self._get_response(make_discover(hwaddr))
        asserts.assert_false(None == resp,
            "Device did not reply to first DHCP discover")
        self.server_addr = getopt(resp, 'server_id')
        asserts.assert_false(None == self.server_addr,
            "DHCP server did not specify server identifier")
        # Ensure that we don't depend on assigned route/gateway on the host
        conf.route.add(host=self.server_addr, dev=self.iface, gw="0.0.0.0")

    def setup_test(self):
        # Some versions of scapy do not close the receive file properly
        warnings.filterwarnings("ignore", category=ResourceWarning)

        bind_layers(UDP, BOOTP, dport=68)
        self.hwaddr = self._next_hwaddr()
        self.other_hwaddr = self._next_hwaddr()
        self.cleanup_releases = []

    def teardown_test(self):
        for packet in self.cleanup_releases:
            self._send(packet)

    def teardown_class(self):
        self.stop_arp.set()
        self._stop_usb_tethering(self.dut)

    def _start_usb_tethering(self, dut):
        """ Start USB tethering

        Args:
            1. dut - ad object
        """
        self.log.info("Starting USB Tethering")
        dut.stop_services()
        dut.adb.shell(pmc_start_usb_tethering_cmd)
        self.USB_TETHERED = True

    def _stop_usb_tethering(self, dut):
        """ Stop USB tethering

        Args:
            1. dut - ad object
        """
        self.log.info("Stopping USB Tethering")
        dut.adb.shell(pmc_stop_usb_tethering_cmd)
        self._wait_for_device(self.dut)
        dut.start_services(skip_sl4a=getattr(dut, "skip_sl4a", False))
        self.USB_TETHERED = False

    def _wait_for_device(self, dut):
        """ Wait for device to come back online

        Args:
            1. dut - ad object
        """
        while dut.serial not in android_device.list_adb_devices():
            pass
        dut.adb.wait_for_device()

    def _wait_for_new_iface(self, old_ifaces):
        old_set = set(old_ifaces)
        # Try 10 times to find a new interface with a 1s sleep every time
        # (equivalent to a 9s timeout)
        for i in range(0, 10):
            new_ifaces = set(get_if_list()) - old_set
            asserts.assert_true(len(new_ifaces) < 2,
                "Too many new interfaces after turning on tethering")
            if len(new_ifaces) == 1:
                return new_ifaces.pop()
            time.sleep(1)
        asserts.fail("Timeout waiting for tethering interface on host")

    def _sniff_arp(self, stop_arp):
        try:
            sniff(iface=self.iface, filter='arp', prn=self._handle_arp, store=0,
                stop_filter=lambda p: stop_arp.is_set())
        except:
            # sniff may raise when tethering is disconnected. Ignore
            # exceptions if stop was requested.
            if not stop_arp.is_set():
                raise

    def _handle_arp(self, packet):
        # Reply to all arp "who-has": say we have everything
        if packet[ARP].op == ARP.who_has:
            reply = ARP(op=ARP.is_at, hwsrc=self.real_hwaddr, psrc=packet.pdst,
                hwdst=BROADCAST_MAC, pdst=SUBNET_BROADCAST)
            sendp(Ether(dst=BROADCAST_MAC, src=self.real_hwaddr) / reply,
                iface=self.iface, verbose=False)

    def test_config_assumptions(self):
        resp = self._get_response(make_discover(self.hwaddr))
        asserts.assert_false(None == resp, "Device did not reply to discover")
        asserts.assert_true(get_yiaddr(resp).startswith(NETADDR_PREFIX),
            "Server does not use expected prefix")

    def test_discover_assigned_ownaddress(self):
        addr, siaddr, resp = self._request_address(self.hwaddr)

        lease_time = getopt(resp, 'lease_time')
        server_id = getopt(resp, 'server_id')
        asserts.assert_true(lease_time > 10, "Lease time is unreasonably short")
        asserts.assert_false(addr == '0.0.0.0', "Assigned address is empty")
        # Wait to test lease expiration time change
        time.sleep(2)

        # New discover, same address
        resp = self._get_response(make_discover(self.hwaddr))
        # Lease time renewed: exptime not decreased
        asserts.assert_equal(lease_time, getopt(resp, 'lease_time'))
        asserts.assert_equal(addr, get_yiaddr(resp))

    def test_discover_assigned_otherhost(self):
        addr, siaddr, _ = self._request_address(self.hwaddr)

        # New discover, same address, different client
        resp = self._get_response(make_discover(self.other_hwaddr,
            [('requested_addr', addr)]))

        self._assert_offer(resp)
        asserts.assert_false(get_yiaddr(resp) == addr,
            "Already assigned address offered")

    def test_discover_requestaddress(self):
        addr = NETADDR_PREFIX + '200'
        resp = self._get_response(make_discover(self.hwaddr,
            [('requested_addr', addr)]))
        self._assert_offer(resp)
        asserts.assert_equal(get_yiaddr(resp), addr)

        # Lease not committed: can request again
        resp = self._get_response(make_discover(self.other_hwaddr,
            [('requested_addr', addr)]))
        self._assert_offer(resp)
        asserts.assert_equal(get_yiaddr(resp), addr)

    def _assert_renews(self, request, addr, expTime):
        time.sleep(2)
        resp = self._get_response(request)
        self._assert_ack(resp)
        asserts.assert_equal(addr, get_yiaddr(resp))
        # Lease time renewed
        asserts.assert_equal(expTime, getopt(resp, 'lease_time'))

    def test_request_wrongnet(self):
        resp = self._get_response(make_request(self.hwaddr,
            OTHER_NETADDR_PREFIX + '1', None))
        self._assert_nak(resp)

    def test_request_inuse(self):
        addr, siaddr, _ = self._request_address(self.hwaddr)
        res = self._get_response(make_request(self.other_hwaddr, addr, None))
        self._assert_nak(res)

    def test_request_initreboot(self):
        addr, siaddr, resp = self._request_address(self.hwaddr)
        exp = getopt(resp, 'lease_time')

        # siaddr NONE: init-reboot client state
        self._assert_renews(make_request(self.hwaddr, addr, None), addr, exp)

    def test_request_initreboot_nolease(self):
        # RFC2131 #4.3.2
        asserts.skip("dnsmasq not compliant if --dhcp-authoritative set.")
        addr = NETADDR_PREFIX + '123'
        resp = self._get_response(make_request(self.hwaddr, addr, None))
        asserts.assert_equal(resp, None)

    def test_request_initreboot_incorrectlease(self):
        otheraddr = NETADDR_PREFIX + '123'
        addr, siaddr, _ = self._request_address(self.hwaddr)
        asserts.assert_false(addr == otheraddr,
            "Test assumption not met: server assigned " + otheraddr)

        resp = self._get_response(make_request(self.hwaddr, otheraddr, None))
        self._assert_nak(resp)

    def test_request_rebinding(self):
        addr, siaddr, resp = self._request_address(self.hwaddr)
        exp = getopt(resp, 'lease_time')

        self._assert_renews(make_request(self.hwaddr, None, None, ciaddr=addr),
            addr, exp)

    def test_request_rebinding_inuse(self):
        addr, siaddr, _ = self._request_address(self.hwaddr)

        resp = self._get_response(make_request(self.other_hwaddr, None, None,
            ciaddr=addr))
        self._assert_nak(resp)

    def test_request_rebinding_wrongaddr(self):
        otheraddr = NETADDR_PREFIX + '123'
        addr, siaddr, _ = self._request_address(self.hwaddr)
        asserts.assert_false(addr == otheraddr,
            "Test assumption not met: server assigned " + otheraddr)

        resp = self._get_response(make_request(self.hwaddr, None, None,
            ciaddr=otheraddr))
        self._assert_nak(resp)
        self._assert_broadcast(resp)

    def test_request_rebinding_wrongaddr_relayed(self):
        otheraddr = NETADDR_PREFIX + '123'
        relayaddr = NETADDR_PREFIX + '124'
        addr, siaddr, _ = self._request_address(self.hwaddr)
        asserts.assert_false(addr == otheraddr,
            "Test assumption not met: server assigned " + otheraddr)
        asserts.assert_false(addr == relayaddr,
            "Test assumption not met: server assigned " + relayaddr)

        req = make_request(self.hwaddr, None, None, ciaddr=otheraddr)
        req.getlayer(BOOTP).giaddr = relayaddr

        resp = self._get_response(req)
        self._assert_nak(resp)
        self._assert_unicast(resp, relayaddr)

    def test_release(self):
        addr, siaddr, _ = self._request_address(self.hwaddr)
        # Re-requesting fails
        resp = self._get_response(make_request(self.other_hwaddr, addr, siaddr))
        self._assert_nak(resp)

        # Succeeds after release
        self._send(make_release(self.hwaddr, addr, siaddr))
        time.sleep(1)
        resp = self._get_response(make_request(self.other_hwaddr, addr, siaddr))
        self._assert_ack(resp)

    def test_release_noserverid(self):
        addr, siaddr, _ = self._request_address(self.hwaddr)

        # Release without server_id opt ignored
        release = make_release(self.hwaddr, addr, siaddr)
        removeopt(release, 'server_id')
        self._send(release)

        # Not released: request fails
        resp = self._get_response(make_request(self.other_hwaddr, addr, siaddr))
        self._assert_nak(resp)

    def test_release_wrongserverid(self):
        addr, siaddr, _ = self._request_address(self.hwaddr)

        # Release with wrong server id
        release = make_release(self.hwaddr, addr, siaddr)
        setopt(release, 'server_id', addr)
        self._send(release)

        # Not released: request fails
        resp = self._get_response(make_request(self.other_hwaddr, addr, siaddr))
        self._assert_nak(resp)

    def _request_address(self, hwaddr):
        resp = self._get_response(make_discover(self.hwaddr))
        self._assert_offer(resp)
        addr = get_yiaddr(resp)
        siaddr = getopt(resp, 'server_id')
        resp = self._get_response(make_request(self.hwaddr, addr, siaddr))
        self._assert_ack(resp)
        return addr, siaddr, resp

    def _get_response(self, packet):
        resp = srp1(packet, iface=self.iface, timeout=10, verbose=False)
        bootp_resp = (resp or None) and resp.getlayer(BOOTP)
        if bootp_resp != None and get_mess_type(bootp_resp) == ACK:
            # Note down corresponding release for this request
            release = make_release(bootp_resp.chaddr, bootp_resp.yiaddr,
                getopt(bootp_resp, 'server_id'))
            self.cleanup_releases.append(release)
        return resp

    def _send(self, packet):
        sendp(packet, iface=self.iface, verbose=False)

    def _assert_type(self, packet, tp):
        asserts.assert_false(None == packet, "No packet")
        asserts.assert_equal(tp, get_mess_type(packet))

    def _assert_ack(self, packet):
        self._assert_type(packet, ACK)

    def _assert_nak(self, packet):
        self._assert_type(packet, NAK)

    def _assert_offer(self, packet):
        self._assert_type(packet, OFFER)

    def _assert_broadcast(self, packet):
        asserts.assert_false(None == packet, "No packet")
        asserts.assert_equal(packet.getlayer(Ether).dst, BROADCAST_MAC)
        asserts.assert_equal(packet.getlayer(IP).dst, NETADDR_BROADCAST)
        asserts.assert_equal(packet.getlayer(BOOTP).flags, 0x8000)

    def _assert_unicast(self, packet, ipAddr=None):
        asserts.assert_false(None == packet, "No packet")
        asserts.assert_false(packet.getlayer(Ether).dst == BROADCAST_MAC,
            "Layer 2 packet destination address was broadcast")
        if ipAddr:
            asserts.assert_equal(packet.getlayer(IP).dst, ipAddr)

    def _next_hwaddr(self):
        addr = make_hwaddr(self.next_hwaddr_index)
        self.next_hwaddr_index = self.next_hwaddr_index + 1
        return addr


def setopt(packet, optname, val):
    dhcp = packet.getlayer(DHCP)
    if optname in [opt[0] for opt in dhcp.options]:
        dhcp.options = [(optname, val) if opt[0] == optname else opt
            for opt in dhcp.options]
    else:
        # Add before the last option (last option is "end")
        dhcp.options.insert(len(dhcp.options) - 1, (optname, val))


def getopt(packet, key):
    opts = [opt[1] for opt in packet.getlayer(DHCP).options if opt[0] == key]
    return opts[0] if opts else None


def removeopt(packet, key):
    dhcp = packet.getlayer(DHCP)
    dhcp.options = [opt for opt in dhcp.options if opt[0] != key]


def get_yiaddr(packet):
    return packet.getlayer(BOOTP).yiaddr


def get_mess_type(packet):
    return getopt(packet, 'message-type')


def make_dhcp(src_hwaddr, options, ciaddr='0.0.0.0', ipSrc='0.0.0.0',
        ipDst=NETADDR_BROADCAST):
    broadcast = (ipDst == NETADDR_BROADCAST)
    ethernet = Ether(dst=BROADCAST_MAC) if broadcast else Ether()
    ip = IP(src=ipSrc, dst=ipDst)
    udp = UDP(sport=68, dport=SERVER_PORT)
    bootp = BOOTP(chaddr=src_hwaddr, ciaddr=ciaddr,
        flags=(0x8000 if broadcast else 0), xid=RandInt())
    dhcp = DHCP(options=options)
    return ethernet / ip / udp / bootp / dhcp


def make_discover(src_hwaddr, options = []):
    opts = [('message-type','discover')]
    opts.extend(options)
    opts.append('end')
    return make_dhcp(src_hwaddr, options=opts)


def make_request(src_hwaddr, reqaddr, siaddr, ciaddr='0.0.0.0', ipSrc=None):
    if ipSrc == None:
        ipSrc = ciaddr
    opts = [('message-type', 'request')]
    if siaddr:
        opts.append(('server_id', siaddr))
    if reqaddr:
        opts.append(('requested_addr', reqaddr))
    opts.append('end')
    return make_dhcp(src_hwaddr, options=opts, ciaddr=ciaddr, ipSrc=ciaddr)


def make_release(src_hwaddr, addr, server_id):
    opts = [('message-type', 'release'), ('server_id', server_id), 'end']
    return make_dhcp(src_hwaddr, opts, ciaddr=addr, ipSrc=addr, ipDst=server_id)


def make_hwaddr(index):
    if index > 0xffff:
        raise ValueError("Address index out of range")
    return '\x44\x85\x00\x00{}{}'.format(chr(index >> 8), chr(index & 0xff))


def format_hwaddr(addr):
    return  ':'.join(['%02x' % ord(c) for c in addr])
