see [Stickpile-DocoCD for how to deploy](https://github.com/pcs3rd/stickpile_doco-cd)  
Meant to be deployed on a host from my nix-config repo.

# Need to make changes?

## Step 1: Check out this git repo, or open it in [github.dev](https://github.com/pcs3rd/stickpile_compose-config)
```
$ git clone https://github.com/pcs3rd/stickpile_compose-config.git
```

## Step 2: Make your changes.
If access to SOPS-encrypted secrets are needed, please reach out to the local server administrator for access.
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
