# Debug setup for Visual Studio Code

If you already have a launch.json, merge the below config, otherwise:

go to `Run and Debug` tab on sidebar

click link text `create a launch.json file` 

select: `Python`

select: `Remote Attach`

Enter the host name... : `localhost`

Enter the port number... : `5678`

your launch.json should look like below
```
{
	// Use IntelliSense to learn about possible attributes.
	// Hover to view descriptions of existing attributes.
	// For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
	"version": "0.2.0",
	"configurations": [
		{
			"name": "Python: Remote Attach",
			"type": "python",
			"request": "attach",
			"connect": {
				"host": "localhost",
				"port": 5678
			},
			"pathMappings": [
				{
					"localRoot": "${workspaceFolder}",
					"remoteRoot": "."
				}
			],
			"justMyCode": true
		}
	]
}
```

## How it's working

When you use

`docker-compose up` - `gamechanger-ml/gamechangerml/api/docker-compose.yml`

This exposes port `5678` for `gamechanger-ml-gpu`

<br>

In the entrypoint `gamechanger-ml/gamechangerml/api/fastapi/mlapp.py`

`debug_if_flagged()` is called immediately, which is from `gamechanger-ml/gamechangerml/debug/debug_connector.py`

This starts up `debugpy` to listen on `5678` if the ENV variable `ENABLE_DEBUGGER` in `setup_env.sh` is set to `true`

The vscode debugger will attach to it using `launch.json` config

Now you're ready to crush bugs 🥾🦟