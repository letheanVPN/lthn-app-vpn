
import {LetheanBackend} from './daemons/lthn/lethean-backend.ts';
import {LetheanCli} from './lethean-cli.ts';
import {LetheanDaemonLetheand} from './daemons/lthn/letheand.ts';

switch (Deno.args[0]){
	case 'backend':
		new LetheanBackend();
		break;
	case 'letheand':
		LetheanDaemonLetheand.init();
		break;
	default:
		LetheanCli.init();
		break;
}


