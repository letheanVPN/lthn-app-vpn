import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import {LetheanDaemonLetheand} from './lthn/letheand.ts';

export class LetheanDaemons {


	public static config() {
		return new Command().description('Lethean Binary Control')
			.command('chain', LetheanDaemonLetheand.config())
			.command('wallet', 'Wallet CLI')
			;

//		# Initialise config
	}
}
