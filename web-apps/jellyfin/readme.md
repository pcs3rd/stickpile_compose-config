## Network Config. 
Macvlan isn't scoped on swarm or whatever. 
We need to make them ourselves
```
docker network create --config-only --subnet 192.168.187.160/29 --gateway 192.168.187.162 -o parent=enp0s20f0u4 --ip-range 192.168.187.160/29 zdvr1
```
```
docker network create --config-only --subnet 192.168.83.64/29 --gateway 192.168.83.66 -o parent=enp0s20f0u4 --ip-range 192.168.83.64/29 zdvr2
```
