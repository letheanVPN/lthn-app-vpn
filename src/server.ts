import {LetheanCli} from './lethean-cli.ts';
// @todo adds stdin/tcp detection for rest mapping
await LetheanCli.init();
try {
	let args = ['--help'];
	if (Deno.args.length > 1) {
		args = Deno.args;
	}
	await LetheanCli.run(args);
} catch (error) {

	console.log(error.message);
	Deno.exit(0);
}


