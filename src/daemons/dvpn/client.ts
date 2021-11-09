import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';

export class LetheanDaemonDvpnClient {

	public static config() {
		return new Command().description('VPN Client Control')
			.option('--user <string>', 'Switch privileges to this user')
			.option('--group <string>', 'Switch privileges to this group')
			.option('--chroot <string>', 'Chroot to prefix')
			.option('--refresh-time <number>', 'Refresh frequency. Set to 0 for disable autorefresh.')
			.option('--save-time <number>', 'Save authid frequency. Use 0 to not save authid regularly.')
			.option('--max-wait-to-spend <number>', 'When payment arrive, we will wait max this number of seconds for first session before spending credit.')
			.option('--run-services <boolean>', 'Run services from dispatcher or externally. Default to run by itnsdispatcher.')
			.option('--track-sessions <boolean>', 'If true, dispatcher will track sessions. If not, existing sessions will not be terminated after payment is spent.')
			.option('-S, --generate-server-configs  <boolean>', 'Generate configs for services and exit')
			.option('-H, --from-height <number>', 'Initial height to start scan payments. Default is actual height.')
			.option('--no-check-wallet-rpc  <boolean>', 'Do not check wallet collection at start.')
			.option('--wallet-rpc-uri <string>', 'Wallet RPC URI')
			.option('--wallet-username <string>', 'Wallet RPC username')
			.option('--wallet-password  <string>', 'Wallet RPC passwd')
			.option('--provider-key  <string>', 'ProviderID (private ed25519 key)');
	}
}
