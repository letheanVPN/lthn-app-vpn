# Welcome to Lethean VPN

This project provides the interface into the VPN Marketplace.

For full documentation visit [https://vpn.lethean.help](https://vpn.lethean.help).

## Commands

* `make config` - Create a VPN exit node configuration
* `make run` - same as `lthn/vpn run`

### Dev Commands
* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml       # Documentation Config.
    docs/
        index.md     # The documentation homepage.
    scripts/         # Utility scripts for VPN ops
    settings/        # user editable configurations
    src/
        client/      # VPN Client scipts
        conf/        # Default configuration templates
        lib/         # LetheanVPN Interfaces
        server/      # VPN Server scripts
        templates/   # Dispatcher & SDP Defaults
        ...      
