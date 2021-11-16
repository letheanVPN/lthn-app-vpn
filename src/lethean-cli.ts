import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import {CompletionsCommand} from 'https://deno.land/x/cliffy/command/completions/mod.ts';
import {HelpCommand} from 'https://deno.land/x/cliffy/command/help/mod.ts';
import {RestService} from './daemons/rest.service.ts';
import {LetheanDaemons} from './daemons/lethean-daemons.ts';
import {LetheanAccount} from './accounts/user.ts';
import {LetheanUpdater} from './tools/updater.ts';
import {Filesystem} from './tools/filesystem.ts';

export class LetheanCli {

	static options: any;

	constructor() {

	}

	static async run(args: any) {
		return await LetheanCli.options.parse(args);
	}

	static async init() {
		LetheanCli.options = await new Command()
			.name('lthn')
			.version('0.1.0')
			.description('Command line interface for Lethean')
			.command('daemon', LetheanDaemons.config())
			.command('update', LetheanUpdater.config())
			.command('backend', RestService.config())
			.command('filesystem', Filesystem.config())
			.command('account', LetheanAccount.config())
			//			.command("vpn",
			//				new Command().description('VPN Functions')
			//						.command('provider', LetheanToolsProvider.config()
			//						.command('client', LetheanDaemonDvpnClient.config())
			//					))
			.command('help', new HelpCommand())
			.command('completions', new CompletionsCommand());


	}

}
