import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';

export class LetheanDaemonDvpnClient {

	public static config() {
		return new Command().description('VPN Client Control')
			.option('--user', 'Switch privileges to this user')
			.option('--group', 'Switch privileges to this group')
			.option('--chroot', 'Chroot to prefix')
			.option('--refresh-time', 'Refresh frequency. Set to 0 for disable autorefresh.')
			.option('--save-time', 'Save authid frequency. Use 0 to not save authid regularly.')
			.option('--max-wait-to-spend', 'When payment arrive, we will wait max this number of seconds for first session before spending credit.')
			.option('--run-services', 'Run services from dispatcher or externally. Default to run by itnsdispatcher.')
			.option('--track-sessions', 'If true, dispatcher will track sessions. If not, existing sessions will not be terminated after payment is spent.')
			.option('-S, --generate-server-configs', 'Generate configs for services and exit')
			.option('-H, --from-height', 'Initial height to start scan payments. Default is actual height.')
			.option('--no-check-wallet-rpc', 'Do not check wallet collection at start.')
			.option('--wallet-rpc-uri', 'Wallet RPC URI')
			.option('--wallet-username', 'Wallet RPC username')
			.option('--wallet-password', 'Wallet RPC passwd')
			.option('--provider-key', 'ProviderID (private ed25519 key)')
			;

//		# Initialise config
	}
}
