import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import {LetheanDaemonLetheand} from './lthn/letheand.ts';
import {LetheanWalletRpc} from './lthn/lethean-wallet-rpc.ts';
import {LetheanWalletVpnRpc} from './lthn/lethean-wallet-vpn-rpc.ts';

export class LetheanDaemons {


	public static config() {
		return new Command().description('Lethean Binary Control')
			.command('chain', LetheanDaemonLetheand.config())
			.command('wallet', LetheanWalletRpc.config())
			;

	}
}
