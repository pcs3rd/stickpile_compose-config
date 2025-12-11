## Network Config. 
Macvlan isn't scoped on swarm or whatever. 
We need to make them ourselves
```
docker network create --config-only -d ipvlan --subnet 192.168.187.160/29 --gateway 192.168.187.161 -o parent=enp0s20f0u4 -o ipvlan_mode=l2 --ip-range 192.168.187.160/29 zdvr1
```
```
docker network create --config-only -d ipvlan --subnet 192.168.83.64/29 --gateway 192.168.83.65 -o parent=enp0s20f0u5 -o ipvlan_mode=l2 --ip-range 192.168.83.64/29 zdvr2
```
```
docker network create -d macvlan --scope swarm --config-from zdvr1 swarm-zdvr1
```
```
docker network create -d macvlan --scope swarm --config-from zdvr2 swarm-zdvr2
```