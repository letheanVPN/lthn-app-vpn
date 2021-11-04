import {LetheanCli} from './lethean-cli.ts';
// @todo adds stdin/tcp detection for rest mapping
await LetheanCli.init();
await LetheanCli.run(Deno.args);


