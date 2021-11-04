import { Command } from "https://deno.land/x/cliffy/command/mod.ts";
import { CompletionsCommand } from "https://deno.land/x/cliffy/command/completions/mod.ts";
import { HelpCommand } from "https://deno.land/x/cliffy/command/help/mod.ts";
import {LetheanToolsProvider} from './tools/provider.ts';
import {LetheanDaemonDvpnClient} from './daemons/dvpn/client.ts';
import {LetheanBackend} from './daemons/lthn/lethean-backend.ts';
import {LetheanDaemons} from './daemons/lethean-daemons.ts';
import {LetheanAccount} from './accounts/user.ts';
import {LetheanUpdater} from './tools/updater.ts';
import {Filesystem} from './tools/filesystem.ts';

export class LetheanCli {

	static options: any
	 constructor() {

	}

	static async run(args: any){
		try {
			LetheanCli.options.parse(args);
		} catch (error) {
			console.error("[CUSTOM_ERROR]", error);
			Deno.exit(1);
		}
	}

	static async init() {
		LetheanCli.options = await new Command()
			.name("lthn")
			.version("0.1.0")
			.description("Command line interface for Lethean")
			.option('--home-dir', 'Home directory', {global: true, default: '~/Lethean'})
			.option('--bin-dir', 'Binaries directory', {global: true, default: '~/Lethean/cli'})
			.command('backend', LetheanBackend.config())
			.command('filesystem', Filesystem.config())
			.command('account', LetheanAccount.config())
			.command('daemon', LetheanDaemons.config())
			.command('update', LetheanUpdater.config())
//			.command("vpn",
//				new Command().description('VPN Functions')
//						.command('provider', LetheanToolsProvider.config()
//						.command('client', LetheanDaemonDvpnClient.config())
//					))
			.command("help", new HelpCommand())
			.command("completions", new CompletionsCommand());


	}

}
