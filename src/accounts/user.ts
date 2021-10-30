import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import { createRequire } from "https://deno.land/std/node/module.ts";


export class LetheanAccount {

    public static async create(args: any) {
		console.log('yo')
		console.log(args)
//		const { privateKey, publicKey, revocationCertificate } = await openpgp.generateKey({
//			type: 'rsa', // Type of the key, defaults to ECC
//			rsaBits: 4096,
//			userIDs: [{name: args.username}], // you can pass multiple user IDs
//			passphrase: args.password, // protects the private key
//			format: 'armored' // output key format, defaults to 'armored' (other options: 'binary' or 'object')
//		})
//
//			console.log( privateKey, publicKey, revocationCertificate )

	}


	public static config() {
		return new Command().description('Lethean Account Management')
			.command('create', 'Create an Account on the filesystem')
			.option('-n, --name <string>', 'Username to use')
			.option('-p, --password <string>', 'Password')
			.action((args) => LetheanAccount.create(args))
			;

//		# Initialise config
	}

}
