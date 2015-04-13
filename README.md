# Supercharging IP routers using SDN switches

- Install Virtualbox
- Install Ubuntu Server
- Install Openvswitch
- Install SDN controller
- Install Dynamips/Dynagen (https://github.com/GNS3/dynamips)
- Check that you have OVS installed already
- Create virtual interfaces:

```
udo ovs-vsctl del-br br0

sudo ip tuntap add mode tap vnet0
sudo ip tuntap add mode tap vnet1
sudo ip tuntap add mode tap vnet2

sudo ifconfig vnet0 up
sudo ifconfig vnet1 up
sudo ifconfig vnet2 up

sudo ovs-vsctl add-br br0
sudo ovs-vsctl add-port br0 vnet0
sudo ovs-vsctl add-port br0 vnet1
sudo ovs-vsctl add-port br0 vnet2
sudo ovs-vsctl set-controller br0 tcp:127.0.0.1:6633
sudo ovs-vsctl set-fail-mode br0 secure
sudo ifconfig br0 10.0.0.3/24 up
```
- Always verify that the interfaces are up and running, as well as the bridge, before launching the routers

- Create the three virtual hosts. One virtual host behind each router.

```
# making sure that IP forwarding is activated
sudo sysctl -w net.ipv4.ip_forward=1

# virtual interfaces that serve to connect the routers to the OF switch
sudo ip netns add r1_host
sudo ip netns add r2_host
sudo ip netns add r3_host

sudo ip netns list

sudo ip netns exec r1_host ip link set dev lo up
sudo ip netns exec r2_host ip link set dev lo up
sudo ip netns exec r3_host ip link set dev lo up

sudo ip link add veth_r1_host type veth peer name veth_r1
sudo ip link add veth_r2_host type veth peer name veth_r2
sudo ip link add veth_r3_host type veth peer name veth_r3

sudo ip link set veth_r1_host netns r1_host
sudo ip link set veth_r2_host netns r2_host
sudo ip link set veth_r3_host netns r3_host

# configure IP address on the hosts
sudo ip netns exec r1_host ip addr add 1.0.0.2/24 dev veth_r1_host
sudo ip netns exec r1_host ip link set dev veth_r1_host up

sudo ip netns exec r2_host ip addr add 2.0.0.2/24 dev veth_r2_host
sudo ip netns exec r2_host ip link set dev veth_r2_host up

sudo ip netns exec r3_host ip addr add 3.0.0.2/24 dev veth_r3_host
sudo ip netns exec r3_host ip link set dev veth_r3_host up

# activate the virtual interface on the router side
sudo ip link set dev veth_r1 up
sudo ip link set dev veth_r2 up
sudo ip link set dev veth_r3 up

# configure routing on the virtual host to point towards the router
sudo ip netns exec r1_host route add default gw 1.0.0.1 veth_r1_host
sudo ip netns exec r2_host route add default gw 2.0.0.1 veth_r2_host
sudo ip netns exec r3_host route add default gw 3.0.0.1 veth_r3_host
```

- Run dynamips with "sudo dynamips -H 7200"

- Install GNS3 for dynagen
	- http://sourceforge.net/projects/gns-3/files/GNS3/0.8.7/GNS3-0.8.7-src.tar.gz/download
	- python ~/GNS3-0.8.7/src/GNS3/Dynagen/dynagen.py dynagen.net (if install in home directory)

- Once in the dynagen CLI, use start /all to start all the routers, before that, you can import a configuration with the command import

- Start an SDN controller

```
cd pox
./pox forwarding.l2_learning
```

- To launch ExaBGP:
```
cd /home/lvanbever/sdx/exabgp/etc/exabgp/rs
sudo env exabgp.tcp.bind="127.0.0.1" exabgp.tcp.port=179 /home/lvanbever/sdx/exabgp/sbin/exabgp exabgp-rs.conf
```

To test the connectivity, create a bash in the namespace of a virtual host (for instance r1)
```
sudo ip netns exec r1_host bash
```

From there, you should be able to ping the others virtual host :
```
ping 2.0.0.2
ping 3.0.0.2
```
