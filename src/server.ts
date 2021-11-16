import {LetheanCli} from './lethean-cli.ts';
// @todo adds stdin/tcp detection for rest mapping
await LetheanCli.init();
try {
	let args;
	if (Deno.args.length === 0) {
		args = ['--help'];
	} else {
		args = Deno.args;
	}
	await LetheanCli.run(args);
} catch (error) {

	console.log(error.message);
	Deno.exit(0);
}


