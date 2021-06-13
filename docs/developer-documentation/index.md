# VPN Overview

The `lthn` VPN dispatcher is a tool that orchestrates all other modules (proxy, VPN, config, etc.). It does not provide any VPN functionality by itself.
The dispatcher uses system packages whenever possible but it runs all instances manually after invoking.
More info about technical design can be found in the [Lethean Whitepapers](https://lethean.io/vpn-whitepaper/)

When our docker image is used, system packages are no longer used, we utilize the host networking system to provide the services over the network, regardless of host operating system.

## Runtime Modes

### Client mode
As a client, The `lthn` dispatcher uses global SDP platform to fetch data about a provider and gather connection details. Currently, there is no automatic payment functionality inside client. It is up to user to send corresponding payments from their wallet to the VPN provider.

Our systems show only instructions on how to pay due to limitations of providing a non-fungable VPN payment system.


### Server mode

As a server, dispatcher helps you to create, publish and run your service as a provider.


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
