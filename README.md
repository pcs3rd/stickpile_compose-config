see [Stickpile-DocoCD for how to deploy](https://github.com/pcs3rd/stickpile_doco-cd)  
Meant to be deployed on a host from my nix-config repo.

# Need to make changes?

## Step 1: Check out this git repo, or open it in [github.dev](https://github.dev/pcs3rd/stickpile_compose-config)
```
$ git clone https://github.com/pcs3rd/stickpile_compose-config.git
```

## Step 2: Create a new branch, and make your changes.
If access to SOPS-encrypted secrets are needed, please reach out to the local server administrator for assistance.
The linked repo has some further hints on decrypting these files for writing.

## Step 3: Push to github. 
### Via github.dev/visual studio code
Go ahead and commit (make sure to include a commit message), and then push/sync. 
### Via git cli

#### Add any new files to git. 
```
$ git add <path/to/file>
```
#### Make a code commit
```
$ git commit -m "What changes did I make?
```
#### Push the code commit
```
$ git push 
```
#### DONE!

## Step 4: Wait.
Depending on the host (and it's configuration), changes may take up to five minutes to propagate.

In the case that websockets are properly configured, changes may propagate more quickly.  
  
---  
Other Documentaition:   
 - [Services Overview](docs/services-overview.md)
 - [Migration Guide](docs/migrating.md)
In the case that websockets are properly configured, changes may propagate more quickly.

# Swarm Node Labels

Services with local volumes or hardware dependencies use placement constraints. When adding a new Swarm node, apply the appropriate labels:

```bash
# Nodes that run the media stack (jellyfin, ersatztv, etc.) — must have a local volume for jellyfin_db
docker node update --label-add role=media <node-name>

# Nodes that run authentik — must have a local volume for postgresql_data
docker node update --label-add role=authentik <node-name>

# Nodes that run seafile — must have a local volume for seafile_db (MariaDB)
docker node update --label-add role=seafile <node-name>

# Nodes with an Intel iGPU (for hardware transcoding)
docker node update --label-add intel.gpu=true <node-name>
```

Manager nodes (`node.role == manager`) are automatically used for Traefik and CrowdSec, which need access to the Swarm API and have local SQLite volumes.

To inspect labels on all nodes:
```bash
docker node ls -q | xargs docker node inspect --format '{{ .Description.Hostname }}: {{ .Spec.Labels }}'
```

# Quick links to files   
- [blocky allowlist.txt](compose/ubnt_console/config/lists/allowlist.txt)
- [blocky denylist.txt](compose/ubnt_console/config/lists/denylist.txt)
- [blocky configuration](compose/ubnt_console/config/config.yml)
