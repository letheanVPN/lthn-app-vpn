import {LetheanCli} from './lethean-cli.ts';
// @todo adds stdin/tcp detection for rest mapping
await LetheanCli.init();
try {
await LetheanCli.run(Deno.args);
} catch (error) {

	console.log(error.message);
	Deno.exit(0);
}


