# Welcome to Lethean VPN

This project provides the interface into the VPN Marketplace.

## Commands

* `make config` - Create a VPN exit node configuration

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
