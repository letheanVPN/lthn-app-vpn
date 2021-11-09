# Lethean Unified Command Line & Rest API

* Deno Cheat Sheet: https://droces.github.io/Deno-Cheat-Sheet/

## Development Flow

In package.json is some NPM scripts, it's just an easy command runner nodejs is not actually used here.

`$HOME/.deno/bin/deno run --allow-net --allow-env --allow-run --allow-read --allow-write --unstable src/server.ts`

I normally adjust the "start" script, but the above is the same as `lthn.exe`, so add `--help` to show the cli
interface. it works just like Docker CLI, subcommands.

`backend start --home-dir=$HOME/Lethean`

Will start TLS enabled server on port 36911, you need to run the GUI once, even if it breaks a self signed SSL is made
for the backend. or make a ssl for localhost and put it here `$HOME/Lethean/conf/public.pem`

once the backend is up, https://localhost:36911 will show the contents of `--help` for GET and will trigger the action
for POST POST data is a json object, not formData.

sub-commands map to url parts, command arguments become post variables in a --snake-case > snakeCase formatting.

Commands map to static class members, which either hold the process, return void or a string as defined in the config()
function for each sub command class.

CMD actions cant return a string, if the command requires a return string `throw new Resonse("string")` the file server
is the simplest demo.
`src/tools/filesystem.ts`

## Install

* Mac/Linux

```shell
curl -fsSL https://gitlab.com/lthn/projects/vpn/node/-/raw/dvpn-v2/install.sh | sh
```

* Windows Powershell

```shell
iwr https://gitlab.com/lthn/projects/vpn/node/-/raw/dvpn-v2/install.ps1 -useb | iex
```

## Base commands

the CLI is sectioned into sub commands, you can add `--help` at any level to the get arguments for that section.

- `lthn update --help`
- `lthn backend start --help`
- `lthn chain start --help`

- `lthn account create --username=test --password=test`

- `lthn update cli`
