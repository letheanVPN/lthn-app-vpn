import { Command } from "https://deno.land/x/cliffy/command/mod.ts";
import { CompletionsCommand } from "https://deno.land/x/cliffy/command/completions/mod.ts";
import { HelpCommand } from "https://deno.land/x/cliffy/command/help/mod.ts";
import {LetheanToolsProvider} from './tools/provider.ts';
export class LetheanCli {

	static options: any
	 constructor() {

	}

	static async init() {
		LetheanCli.options = await new Command()
			.name("lthn")
			.version("0.1.0")
			.description("Command line interface for Lethean")
			.command("vpn",
				new Command().description('VPN Functions')
					.command('provider', LetheanToolsProvider.config()

					))
			.option("-h, --home-dir", "Home directory.")
			.option("-d, --data-dir", "Directory to store data.")
			.option("-c, --config-file", "Daemon config(dep)")
			.option("-b, --bin-dir", "Binaries location")
			.command("help", new HelpCommand())
			.command("completions", new CompletionsCommand())
			.parse(Deno.args);

	}
}
